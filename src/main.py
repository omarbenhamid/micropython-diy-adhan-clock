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
mp3player = UART(2,9600)
spk=Pin(2,Pin.OUT, Pin.PULL_DOWN)

FAJR_ADHAN_FOLDER=const(1)
ALL_ADHAN_FOLDER=const(2)



def _timeout_read(maxtime):
    ret = mp3player.read(1)
    
    while not ret:
        if time.ticks_ms() > maxtime:
            raise Excepton("Timeout reading input")
        time.sleep_ms(100)
        ret = mp3player.read(1)
        
    return ret[0]
    
            
def mp3_query(queryCmd, DL=0x00):
    cmd = yx5300.command_base()
    cmd[3] = queryCmd
    cmd[6] = DL
    # Flush buffer
    while mp3player.read():
        pass
    mp3player.write(cmd)
    
    maxtime = time.ticks_ms() + 1000 # Timeout after one second
    
    c = _timeout_read(maxtime)
    if c != 0x7E: raise Exception("Unexpected header [0] 0x%x : 0x7E expected" % c )
    c = _timeout_read(maxtime)
    if c != 0xFF: raise Exception("Unexpected header [1] 0x%x : 0xFF expected" % c)
    c = _timeout_read(maxtime)
    ret = bytearray(c)
    for i in range(0,c):
        ret[i] = _timeout_read(maxtime)
    c = _timeout_read(maxtime)
    if c != 0xEF: raise Exception("Unexpected tail 0x%x : 0xEF expected" % c)
    
    return ret

def sleepuntilnextsalat():
    """ returns idx when next salat time arrives """
    sidx, stime = sdb.findnextsalat(1)
    delta = stime-time.mktime(localtime())
    
    print("Next salat %s in %d seconds" % (SALATS[sidx], delta))
    # Setup wakeup button
    if delta > 24*60: delta=24*60
    esp32.wake_on_ext0(wbutton, esp32.WAKEUP_ALL_LOW)
    mp3player.write(yx5300.sleep_module())
    machine.deepsleep(delta*1000)

# First initilization

pwm = None
_stopadhan=False
def on_stop_adhan(pin):
    global _stopadhan
    _stopadhan = True
    micropython.schedule(lambda x: mp3player.write(yx5300.stop()),0)

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
    
    mp3player.write(yx5300.wake_module())
    spk.value(1) #Turn on speaker
    time.sleep_ms(200)
    mp3player.write(yx5300.set_volume(30))
    
    if sidx == 0: #Fajr special ringing
        for i in range(1,17):
            led.value(1)
            play_tone(1000,100)
            led.value(0)
            if _stopadhan: return
            time.sleep_ms(300 if i % 4 == 0 else 50)
        led.value(1)
        mp3player.write(yx5300.play_track( urandom.randrange(1,mp3_query(0x4E,DL=FAJR_ADHAN_FOLDER)[3]+1) , FAJR_ADHAN_FOLDER))
    
    else:
        for i in range(0, sidx):
            led.value(1)
            play_tone(800,100)
            led.value(0)
            if _stopadhan: return
            time.sleep_ms(500)
        led.value(1)
        mp3player.write(yx5300.play_track( urandom.randrange(1,mp3_query(0x4E,DL=ALL_ADHAN_FOLDER)[3]+1) , ALL_ADHAN_FOLDER))
    timeout = time.ticks_ms() + 300000 #Max 5 minutes
    
    time.sleep_ms(200)
    while mp3_query(0x42)[3] != 0x01 and (time.ticks_ms() < timeout): #Waiting for playing to start (0x01 see to YX5300 datasheet)
        time.sleep_ms(200)
    while mp3_query(0x42)[3] == 0x01 and (time.ticks_ms() < timeout): #playing state according to YX5300 datasheet
        time.sleep_ms(500)
        
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
    led.value(1)
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
    