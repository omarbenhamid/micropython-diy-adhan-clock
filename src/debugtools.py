'''
Created on 29 sept. 2019
Not forced to load this : just tools for debu
@author: omar
'''

from main import *

def fakeadhan(sidx=3, delaymintues=1, db=None):
    global sdb
    if db == None: db = sdb
    _,mo,da,h,mi,_,_,_ = localtime()
    mi = mi+delaymintues
    db.setstime(mo, da, sidx, '%d:%d' % (h,mi))
    db.save()
    import timesdb
    print("TO CLEANUP THE DB FROM KEY %06d :" % timesdb.minuteofyear(mo, da, h, mi))
    print("> del sdb.db['%06d']" % timesdb.minuteofyear(mo, da, h, mi))
    print("> sdb.save()")
    sleepuntilnextsalat()
    
def lastexception():
    print(open('exception.log').read())