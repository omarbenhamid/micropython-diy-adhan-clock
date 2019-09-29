'''
Created on 29 sept. 2019
Not forced to load this : just tools for debu
@author: omar
'''

from main import *

def adhannextminute(sidx=3, db=None):
    global sdb
    if db == None: db = sdb
    _,mo,da,h,mi,_,_,_ = localtime()
    db.setstime(mo, da, sidx, '%d:%d' % (h,mi+1))
    db.save()
    import timesdb
    print("TO CLEANUP THE DB FROM KEY %06d :" % timesdb.minuteofyear(mo, da, h, mi+1))
    print("> del sdb.db['%06d']" % timesdb.minuteofyear(mo, da, h, mi+1))
    print("> sdb.save()")
    sleepuntilnextsalat()