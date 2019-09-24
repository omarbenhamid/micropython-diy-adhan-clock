import machine
from machine import Pin, RTC
import time
import micropython
from timesdb import SalatDB
##### BLE Update

"""
import bluetooth
bt = bluetooth.Bluetooth()
bt.active(1)
bt.advertise(100, 'MicroPython')
print('----')
tx = bluetooth.Characteristic('6E400002-B5A3-F393-E0A9-E50E24DCCA9E', bluetooth.FLAG_READ|bluetooth.FLAG_NOTIFY)
rx = bluetooth.Characteristic('6E400003-B5A3-F393-E0A9-E50E24DCCA9E', bluetooth.FLAG_WRITE)
def onrecv(characteristic, val):
    val = ''.join(chr(x) for x in value) #FIXME: better way to convert bytearray(b'...') to str
    print(val)
    print("FIXME: set time using some funny protocol")
    ds.init((2019,1,1,1,11,11,11,11,11))

rx.on_update(callback)

s = bt.add_service('6E400001-B5A3-F393-E0A9-E50E24DCCA9E', [tx, rx])
tx.write('foo')


"""



sdb = SalatDB()
ds = RTC()

def waitnextsalat():
    """ returns idx when next salat time arrives """
    sidx, stime = sdb.findnextsalat()
    delta = stime-time.mktime(time.localtime())
    print("Next salat in %d seconds" % delta)
    #time.sleep(delta)
    return sidx

# First initilization

def adhan(sidx):
    print('Salat : %d' % sidx)
    
    
# Setup wificonfig button
def toggle_wifi_config(a):
    import wificonfig
    if wificonfig.is_started():
        print("Turn off wificonfig")
        wificonfig.stop()
    else:
        print("Turn on wificonfig")
        wificonfig.start(ds,sdb)

_last_btn_press = 0
def on_wifi_btn(pin):
    global _last_btn_press
    #DEbounce
    tick=time.ticks_ms() 
    if (tick - _last_btn_press) < 200: return
    _last_btn_press = tick
    micropython.schedule(toggle_wifi_config,0)

wbutton = Pin(14,Pin.IN,Pin.PULL_UP)
wbutton.irq(on_wifi_btn, Pin.IRQ_FALLING,machine.SLEEP|machine.DEEPSLEEP)

#Fixime:  Use timers ar lightsleep prevents any interaction
#while True:
#    adhan(waitnextsalat())
