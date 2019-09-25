import machine
from machine import Pin, PWM, RTC
import time
import micropython
import esp32
from timesdb import SalatDB, SALATS
from util import localtime

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


#Wifi setup button
wbutton = Pin(14,Pin.IN,Pin.PULL_UP)
led=Pin(33, Pin.OUT)
buzzer = Pin(25)

def sleepuntilnextsalat():
    """ returns idx when next salat time arrives """
    sidx, stime = sdb.findnextsalat(1)
    delta = stime-time.mktime(localtime())
    
    print("Next salat %s in %d seconds" % (SALATS[sidx], delta))
    # Setup wakeup button
    if delta > 24*60: delta=24*60
    esp32.wake_on_ext0(wbutton, esp32.WAKEUP_ALL_LOW)
    machine.deepsleep(delta*1000)

# First initilization

pwm = None
def play_tone(freq, durationms=None):
    global pwm
    if freq == 0:
        if pwm != None: pwm.deinit()
        return
    
    if pwm == None:
        pwm = PWM(buzzer, freq, 16992)
    else:
        pwm.init(freq, 16992)
    
    if durationms != None:
        time.sleep_ms(durationms)
        pwm.deinit()

def adhan(sidx):
    print('Adhan %s' % SALATS[sidx])
    
    if sidx == 1: #chorok : beep only
        for i in range(1,10):
            play_tone(900,100)
            time.sleep_ms(300 if i % 3 == 0 else 50)
        return
    
    if sidx == 0: #Fajr special ringing
        for i in range(1,17):
            play_tone(1000,100)
            time.sleep_ms(300 if i % 4 == 0 else 50)
    
    else:
        for i in range(0, sidx):
            play_tone(800,100)
            time.sleep_ms(500)
    
    for i in range(0,3):
        play_tone(262, 600)
        play_tone(440, 200)
        play_tone(247, 600)
        time.sleep_ms(200)
        play_tone(247, 600)
        play_tone(440, 200)
        play_tone(247, 600)
        time.sleep_ms(200)
    
timer = machine.Timer(0)
def turnoff_wificonfig(timer):
    micropython.schedule(lambda x: sleepuntilnextsalat(),0)

_last_btn_press = 0
def on_wifi_btn(pin):
    # End wificonfig session
    global _last_btn_press
    #DEbounce
    tick=time.ticks_ms() 
    if (tick - _last_btn_press) < 200: return
    _last_btn_press = tick
    timer.init(period=500, mode=machine.Timer.ONE_SHOT, callback=turnoff_wificonfig)
    
if machine.wake_reason() == machine.EXT0_WAKE or sdb.isempty():
    # Config button prcessed or no salat times loaded
    import wificonfig
    PWM(led,1)
    wificonfig.start(sdb)
    wbutton.irq(on_wifi_btn, Pin.IRQ_FALLING,machine.SLEEP|machine.DEEPSLEEP)
    print('Wifi config will auto turnoff afeter 5 minutes')
    timer.init(period=5*60000, mode=machine.Timer.ONE_SHOT, callback=turnoff_wificonfig)
    
else:
    #elif machine.wake_reason() == machine.TIMER_WAKE:
    sidx, stime = sdb.findnextsalat()
    print("Next Salat is", sidx, stime)
    currtime = time.mktime(localtime())
    if stime <= currtime and (currtime - stime) < 60:
        adhan(sidx)
    sleepuntilnextsalat() 
    