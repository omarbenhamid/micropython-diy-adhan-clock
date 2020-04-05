'''
Created on 24 sept. 2019

@author: omar
'''

from machine import Pin, RTC

USE_DS_1302=False

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