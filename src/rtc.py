'''
Created on 24 sept. 2019

@author: omar
'''

import config
from machine import Pin, RTC
import wifi
import time

c = config.get("rtc")


USE_DS_1302=c.get("DS1302")
TZ_DELTA_SECS=c.get("timezoneDeltaMinutes")*60


if USE_DS_1302:
    import DS1302
    rtc = DS1302.DS1302(Pin(19),Pin(18),Pin(5))
else:
    rtc = RTC()
    

def localtime():
    if USE_DS_1302:
        y,m,d,dow,h,mi,s = rtc.DateTime()
        if m == 0: 
            raise Exception('Bad RTC Response : %r, is it correctly connected ?' % ((y,m,d,dow,h,mi,s),))
    else:
        y, m, d, dow, h, mi, s, _us = rtc.datetime()
        
    return (y,m,d,h,mi,s,-1,-1)

def settime(y,m,d,dow,h,mi,s):
    if USE_DS_1302:
        rtc.DateTime((y,m,d,dow,h,mi,s))
        rtc.start()
    else:
        rtc.datetime((y,m,d,dow,h,mi,s,0))
        
def ntpsync():
    import ntptime
    h = c.get("ntphost")
    if h: ntptime.host = h
    with wifi:
        y,m,d,h,mi,s,_,_ = time.localtime(ntptime.time()+TZ_DELTA_SECS)
    settime(y,m,d,1,h,mi,s)
    