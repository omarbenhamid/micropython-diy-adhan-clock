'''
Created on 21 sept. 2019

@author: omar
'''
import btree
import time
from rtc import localtime
from micropython import const

SALATS=['Fajr','Chorok', 'Dohr', 'Asr', 'Maghrib', 'Ishaa']
MONTH31=[1,3,5,7,8,10,12]

def dom(month, year=0): #Non bisecstile by default
    """ Days of month, if year is not specified => 29 days for feburary """
    if month == 2: 
        return 29 if year % 4 == 0 else 28
    elif month in MONTH31: 
        return 31
    return 30

def nextday(self, year, month, day):
    """ return (year, month, day) of next day """
    #compute next day
    day=day+1
    if day > dom(month, year):
        day=1
        month = month+1
        if month > 12:
            month = 1
            year = year + 1
    
    return (year, month, day)

def minuteofyear(month,day, h, m):
    d = 0
    for i in range(1, month):
        d += dom(i)
    d += day - 1
    return (d * 24 + h) * 60 + m


def stimekey(month, day, h, m):
    return "%06d" % minuteofyear(month, day, h, m)

LAST_SALAT_KEY=const("999999")

def salarmkey(sidx):
    return "salarm:%02d" % sidx

LAST_ALARM_KEY=const("salarm:99")

### Salat Times Database
        
class SalatDB:
    def __init__(self, dbfile="salatimes.db"):
        try:
            self.f = open(dbfile, "r+b")
        except OSError:
            print("Salat db '",dbfile,"' seems not to exist ? creating a new one")
            self.f = open(dbfile, "w+b")
        self.db = btree.open(self.f)
    
    def isempty(self):
        try:
            next(self.db.keys())
            return False
        except StopIteration:
            return True
        
    def save(self):
        self.db.flush()
    
    def findfirstsalatafter(self, year, month, day, hour, min, failifnotfound=False):
        """ Will return info for next salat a tuple : (salatindex,time) 
            time is in sceonds since epoch"""
        bisextile = year % 4 == 0
        
        for nextsalat in self.db.values(stimekey(month, day, hour, min), LAST_SALAT_KEY):
            sidx,mo,da,h,m = (int(x) for x in nextsalat.split(b','))
            if mo == 2 and da == 29 and not bisextile: continue
            while h >= 24:
                h = h - 24
                year, mo, da = nextday(year, mo, da)
            return (sidx, (year, mo, da, h, m))
        
        # IF we get here means no data found for current yer :
        if failifnotfound: raise Exception("Salat data missing.")
        return self.findfirstsalatafter(year+1,1,1,0,0, True)
    
    def findnextsalat(self, mindelayminutes=0):
        """ REturn the next salat after 'now' """
        
        y,m,d,h,mi,_,_,_ = localtime()
        mi = mi + +mindelayminutes
        
        sidx, (oy, omo, oda, oh, om) = self.findfirstsalatafter(y, m, d, h, mi)
        return sidx, time.mktime((oy, omo, oda, oh, om,0,-1,-1))
    
    def setstime(self, month, day, sidx, stime):
        """ Update salat with given time 
            Format of hourd : "HH:MM" ==> HH can be > 23 (next day isha)
        """
        if month > 12 or month < 1: raise ValueError("Bad value for a month : %d" % month)
        if day > dom(month) or day < 1: raise ValueError("Bad value for a day in month %d : %d" % (month, day))
        try:
            h,m=stime.split(':')
            h=int(h) 
            if h < 0: raise ValueError 
            m=int(m)
            if m < 0 or m > 59: raise ValueError
        except ValueError:
            raise ValueError("Bad time : %s" % stime)
        
        self.db[stimekey(month, day, h, m)]="%d,%d,%d,%d,%d" % (sidx, month, day, h, m)
    
    def importcsv(self, csvlines):
        """Example : MM,DD,FH:FM,CH:CM,DH:DM,AH:AM,MH:MM,IH:IM"""
        for lnum,line in enumerate(csvlines.splitlines()):
            line=line.strip()
            if len(line) == 0: #Empty line
                continue
            items = list(x.strip().strip('"') for x 
                        in line.replace(',',';').split(';'))
            
            if len(items) != 8:
                raise ValueError("line %d : must be 8 Columns" % (lnum+1))
            
            try:
                m = int(items[0])
                d = int(items[1])
            except ValueError:
                raise ValueError("line %d : month or day is not a number" % (lnum+1))
            
            try:
                for idx,stime in enumerate(items[2:]):
                    self.setstime(m,d,idx,stime)
            except ValueError as err:
                raise ValueError("Line %d : bad times ... : %s" % str(err))
        self.save()
        
    def iter_times(self, month):
        """ Iterate over key/value pairs of given month """
        for k,v in self.db.items(stimekey(month, 1, 0, 0), stimekey(month, 32, 23, 0)):
            m = int(self.db[k].split(b',')[1])
            if m == month: yield (k,v)
        
    def import_mawaqit_month(self, month, data):
        """ Convert one month JSON (key = day num value = times) and load it"""
        if type(data) == str: data = json.loads(data)
        #ITerate until first day of following monh
        for k,_ in self.iter_times(month):
            del self.db[k]
            
        #Load new month data
        for day, times in data.items():
            for idx,stime in enumerate(times):
                self.setstime(month, int(day),idx,stime)
        self.save()
        
    
    def getsalarmdelay(self, sidx):
        """ Return salat alarm delay in mutes or none if none set """
        k = salarmkey(sidx)
        if k in self.db : return int(self.db[k])
        else return None
        
    def setsalarm(self, sidx, delayminutes=0):
        """ Set or delete salat alarm : 0 means delete """
        k = salarmkey(sidx)
        
        if delayminutes == 0:
            del self.db[k]
        else:
            self.db[k] = '%02d' % delayminutes
    
        self.save()
    
    def close(self):
        self.db.close()
        self.f.close()
