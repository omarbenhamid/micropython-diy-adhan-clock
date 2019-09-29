'''
Created on 24 sept. 2019

@author: omar
'''

from machine import Pin
import DS1302

ds = DS1302.DS1302(Pin(5),Pin(18),Pin(19))

def localtime():
    y,m,d,dow,h,mi,s = ds.DateTime()
    if m == 0: 
        raise Exception('Bad RTC Response : %r, is it correctly connected ?' % ((y,m,d,dow,h,mi,s),))
    return (y,m,d,h,mi,s,-1,-1)

def settime(y,m,d,dow,h,mi,s):
    ds.DateTime((y,m,d,dow,h,mi,s))
    ds.start()