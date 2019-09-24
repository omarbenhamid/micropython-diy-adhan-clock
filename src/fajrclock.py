import machine
from machine import Pin, PWM, RTC
import time
import micropython
import esp32
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

#Wifi setup button
wbutton = Pin(14,Pin.IN,Pin.PULL_UP)
led=Pin(33, Pin.OUT)

def sleepuntilnextsalat():
    """ returns idx when next salat time arrives """
    sidx, stime = sdb.findnextsalat(1)
    delta = stime-time.mktime(time.localtime())
    print("Next salat in %d seconds" % delta)
    # Setup wakeup button
    esp32.wake_on_ext0(wbutton, esp32.WAKEUP_ALL_LOW)
    machine.deepsleep(delta*1000)

# First initilization

def adhan(sidx):
    print('Salat : %d' % sidx)
    

_last_btn_press = 0
def on_wifi_btn(pin):
    # End wificonfig session
    global _last_btn_press
    #DEbounce
    tick=time.ticks_ms() 
    if (tick - _last_btn_press) < 200: return
    _last_btn_press = tick
    micropython.schedule(lambda x: sleepuntilnextsalat(),0)

    
if machine.wake_reason() == machine.EXT0_WAKE or sdb.isempty():
    # Config button prcessed or no salat times loaded
    import wificonfig
    PWM(led,1)
    wificonfig.start(ds,sdb)
    wbutton.irq(on_wifi_btn, Pin.IRQ_FALLING,machine.SLEEP|machine.DEEPSLEEP)
    print("TODO: set a timer to stop wifi config after N seconds (or maybe n seconds after last request ?")
else:
    #elif machine.wake_reason() == machine.TIMER_WAKE:
    sidx, stime = sdb.findnextsalat()
    print("Next Salat is", sidx, stime)
    currtime = time.mktime(time.localtime())
    if stime < currtime and (currtime - stime) < 60:
        print("Next salat matches current time! FIXME bad test")
        adhan(sidx)
    sleepuntilnextsalat() 
    