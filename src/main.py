import machine
from machine import Pin, PWM, UART
import yx5300
import time
import micropython
from micropython import const
import esp32
from timesdb import SalatDB, SALATS
from rtc import localtime
import urandom
import sys
from audio import AudioPlayer

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
audio = AudioPlayer(UART(2,9600), speaker_pin=Pin(2))

FAJR_ADHAN_FOLDER=const(1)
ALL_ADHAN_FOLDER=const(2)



def sleepuntilnextsalat():
    """ returns idx when next salat time arrives """
    try:
        sidx, stime = sdb.findnextsalat(1)
        delta = stime-time.mktime(localtime())
        
        print("Next salat %s in %d seconds" % (SALATS[sidx], delta))
        # Setup wakeup button
        if delta > 24*60: delta=24*60
        esp32.wake_on_ext0(wbutton, esp32.WAKEUP_ALL_LOW)
        audio.sleep()
        machine.deepsleep(delta*1000)
    except Exception as err:
        led.value(1)
        play_tone(100, 5000)
        with open('exception.log','w') as log:
            sys.print_exception(err,log)
        raise
# First initilization

pwm = None
_stopadhan=False
def on_stop_adhan(pin):
    global _stopadhan
    _stopadhan = True
    micropython.schedule(lambda x: audio.stop(),0)

def play_tone(freq, durationms=None):
    global pwm
    if freq == 0:
        if pwm != None: pwm.deinit()
        return
    if _stopadhan: return
    if pwm == None:
        pwm = PWM(buzzer, freq, 16992)
    else:
        pwm.init(freq, 16992)
    
    if durationms != None:
        time.sleep_ms(durationms)
        pwm.deinit()



def adhan(sidx):
    global _stopadhan
    _stopadhan=False
    wbutton.irq(on_stop_adhan, Pin.IRQ_FALLING,machine.SLEEP|machine.DEEPSLEEP)
    print('Adhan %s' % SALATS[sidx])
    led.value(1)
    if sidx == 1: #chorok : beep only
        for i in range(1,10):
            play_tone(900,100)
            time.sleep_ms(300 if i % 3 == 0 else 50)
            if _stopadhan: return
        return
    
    audio.wakeup()
    audio.volume(30)
    
    if sidx == 0: #Fajr special ringing
        for i in range(1,17):
            led.value(1)
            play_tone(1000,100)
            led.value(0)
            if _stopadhan: return
            time.sleep_ms(300 if i % 4 == 0 else 50)
        led.value(1)
        audio.play_track(FAJR_ADHAN_FOLDER, urandom.randrange(1,audio.query_track_count(FAJR_ADHAN_FOLDER)+1), waitmillis=300000)
        
    
    else:
        for i in range(0, sidx):
            led.value(1)
            play_tone(800,100)
            led.value(0)
            if _stopadhan: return
            time.sleep_ms(500)
        led.value(1)
        audio.play_track(ALL_ADHAN_FOLDER, urandom.randrange(1,audio.query_track_count(ALL_ADHAN_FOLDER)+1), waitmillis=300000)
    
    
    
        
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

try:    
    if machine.wake_reason() == machine.EXT0_WAKE or sdb.isempty():
        # Config button prcessed or no salat times loaded
        led.value(1)
        import wificonfig
        PWM(led,1)
        wificonfig.start(sdb)
        wbutton.irq(on_wifi_btn, Pin.IRQ_FALLING,machine.SLEEP|machine.DEEPSLEEP)
        print('Wifi config will auto turnoff after 5 minutes')
        timer.init(period=5*60000, mode=machine.Timer.ONE_SHOT, callback=turnoff_wificonfig)
        
    else:
        #elif machine.wake_reason() == machine.TIMER_WAKE:
        sidx, stime = sdb.findnextsalat()
        print("Next Salat is", sidx, stime)
        currtime = time.mktime(localtime())
        if stime <= currtime and (currtime - stime) < 60:
            adhan(sidx)
        sleepuntilnextsalat() 
except Exception as err:
    led.value(1)
    play_tone(100, 5000)
    with open('exception.log','w') as log:
        sys.print_exception(err,log)
    