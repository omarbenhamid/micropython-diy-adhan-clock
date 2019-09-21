'''
Created on 21 sept. 2019

@author: omar
'''
import btree
import time

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

### Salat Times Database
        
class SalatDB:
    def __init__(self, dbfile="salatimes.db"):
        try:
            self.f = open(dbfile, "r+b")
        except OSError:
            debug("Salat db '",dbfile,"' seems not to exist ? creating a new one")
            self.f = open(dbfile, "w+b")
        self.db = btree.open(self.f)
    
    
    def findfirstsalatafter(self, year, month, day, hour, min, failifnotfound=False):
        """ Will return info for next salat a tuple : (salatindex,time) 
            time is in sceonds since epoch"""
        for key, stime in self.db.items("%02d-%02d" % (month,day)):
            h,m = (int(x) for x in stime.split(b":"))
            if h < hour: continue #Bad guess
            if h == hour and m <= min: continue #Bad guess
            mo,da,sidx = (int(x) for x in key.split(b'-'))
            while h >= 24:
                h = h - 24
                year, mo, da = nextday(year, mo, da)
            return (sidx, time.mktime((year, mo, da, h, m, 0, -1, -1)))
        
        if failifnotfound: raise Exception("Salat data seems missing.")
        return self.findfirstsalatafter(year+1,1,1,-1,-1, True)
    
    def findnextsalat(self):
        """ REturn the next salat after 'now' """
        y,m,d,h,mi,_,_,_ = time.localtime()
        return self.findfirstsalatafter(y, m, d, h, mi)

    
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
        
        self.db["%02d-%02d-%02d" % (month, day, sidx)]=stime.strip()
    
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
            
    def close(self):
        self.db.close()
        self.f.close()
