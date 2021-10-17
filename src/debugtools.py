'''
Created on 29 sept. 2019
Not forced to load this : just tools for debu
@author: omar
'''
from rtc import localtime

def fakeadhan(sidx=3, delaymintues=1, db=None):
    global sdb
    if db == None: db = sdb
    _,mo,da,h,mi,_,_,_ = localtime()
    mi = mi+delaymintues
    if mi >= 60:
        h = h+1
        mi = mi - 60
    db.setstime(mo, da, sidx, '%d:%d' % (h,mi))
    db.save()
    
    import os
    
    exists = None
    try:
        os.stat('clean.py')
        exists = True
    except:
        exists = False
    
    
    import timesdb
    
    with open('clean.py','a') as c:
        if not exists: 
            c.write("""
import os
def clean(sdb):
    _doclean(sdb)
    sdb.save()
    os.remove('clean.py')
    
def _doclean(sdb):
""")
        c.write("    del sdb.db['%06d']\n" % timesdb.minuteofyear(mo, da, h, mi))
        
    print("To cleanup debug rubish type :")
    print("from clean import clean")
    print("clean(sdb)")
    sleepuntilnextsalat()
    
def lastexception():
    print(open('exception.log').read())