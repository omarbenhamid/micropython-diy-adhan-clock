'''
Created on 21 sept. 2019

@author: omar
'''
import time
from rtc import localtime
from micropython import const
import os
import config

TIMESDB_LOC="/sdcard/times"

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

def salarmkey(sidx):
    return "salat.%02d.alarmDelayMinutes" % sidx



SPEECH_VOL_SIDX=const(99)

def svolumekey(sidx):
    return "salat.%02d.volumeLevel" % sidx

### Salat Times Database
        
class SalatDB:
    def __init__(self, dbdir=TIMESDB_LOC):
        self.dbdir = dbdir if not dbdir.endswith('/') else dbdir[:-1]
        
    
    def isempty(self):
        try:
            files=os.listdir(self.dbdir)
            return len(files) == 0
        except StopIteration:
            return True
        
    def iter_from(self, month, day, hour, min):
        with open("%s/%02d.csv" % (self.dbdir, month),'r') as f:
            for lidx,line in enumerate(f.readlines()):
                da,hours=line.strip().split(',',1)
                try:
                    da=int(da)
                except:
                    if lidx==0: continue #Accept title line ...
                    raise
                if da < day: continue
                for sidx, hm in enumerate(hours.split(',')):
                    h,m=hm.split(':')
                    h=int(h)
                    if da==day and h < hour: continue
                    m=int(m)
                    if da==day and h==hour and m < min: continue
                    yield sidx,month,da,h,m
        if month < 12:
            self.iter_from(month+1,1,0,0)
        
                    
        
    def findfirstsalatafter(self, year, month, day, hour, min, failifnotfound=False):
        """ Will return info for next salat a tuple : (salatindex,time) 
            time is in sceonds since epoch"""
        for sidx,mo,da,h,m in self.iter_from(month, day, hour, min):
            if mo == 2 and da == 29 and not year % 4 == 0: 
                #ignore 29 february for bissexstile year.
                continue
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
    
    def import_csv(self, month, data):
        if month < 1 or month > 12: raise Exception("Bad month")
        
        file="%s/%02d.csv" % (self.dbdir, month)
        with open(file+".tmp" , 'w') as f:
            lastday=0
            for lidx,line in enumerate(data.splitlines()):
                da,hours=line.strip().split(',',2)
                try:
                    da=int(da)
                except:
                    if lidx==0: continue #Accept title line ...
                    raise
                if da != lastday+1: raise Exception("Bad CSV, days not in order")
                lastday=da
                for sidx, hm in enumerate(hours.split(',')):
                    h,m=hm.split(':')
                    h=int(h)
                    m=int(m)
                file.write(line)
                
        os.remove(file)
        os.rename(file+".tmp",file)
    
    def import_mawaqit_month(self, month, data):
        """ Convert one month JSON (key = day num value = times) and load it"""
        if type(data) == str: data = json.loads(data)
        file="%s/%02d.csv" % (self.dbdir, month)
        with open(file+".tmp" , 'w') as f:
            #Load new month data
            for day, times in data.items():
                f.write(str(day))
                f.write(b',')
                f.write(b','.join(times))
        os.remove(file)
        os.rename(file+".tmp",file)
    
    def getsalarmdelay(self, sidx):
        """ Return salat alarm delay in mutes or none if none set """
        k = config.get(salarmkey(sidx), None)
        if k : return int(k)
        else: return None
        
    def setsalarmdelay(self, sidx, delayminutes=0):
        """ Set or delete salat alarm : 0 means delete """
        config.set(salarmkey(sidx), delayminutes)    
    
    def getsvolume(self, sidx):
        """ Return salat alarm delay in mutes or none if none set """
        k = config.get(svolumekey(sidx), 30)
        return int(k)
        
    def setsvolume(self, sidx, volume):
        """ Set or delete salat alarm : 0 means delete """
        if volume < 0 or volume > 30: 
            raise ValueError("Volume must be between 0 and 30")
        config.set(svolumekey(sidx), volume)
        
    def save(self):
        config.save()