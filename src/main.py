import arch
#Turn on led asap
arch.LED_PIN.value(1)

import machine
from machine import Pin, PWM, UART
import time
import micropython
from micropython import const
import esp32
from timesdb import SalatDB, SALATS, SPEECH_VOL_SIDX
from rtc import localtime, ntpsync
import urandom
import sys
import wbuttons
import taskloop


if arch.AUDIO_PLAYER_UART:
    import yx5300_audioplayer as audioplayer
else:
    import adf_audioplayer as audioplayer


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
wbutton = arch.WBUTTON_PIN
volup=arch.VOL_UP_PIN 
voldn=arch.VOL_DN_PIN
led=arch.LED_PIN

player = audioplayer.AudioPlayer(ignoreerrors=True)

FAJR_ADHAN_FOLDER=const(1)
ALL_ADHAN_FOLDER=const(2)

BOOT_LATENCY_SECS=const(30)

def sleepuntilnextsalat(raise_exceptions=True):
    """ returns idx when next salat time arrives """
    try:
        if time.time() < 100000: #Still in year 2000 !
            try:
                ntpsync()
            except:
                pass
        sidx, stime = sdb.findnextsalat(1)
        salm = sdb.getsalarmdelay(sidx)
        
        delta = -1
        if salm != None:
            almtm = stime - (60 * salm)
            delta = almtm-time.mktime(localtime())
            if delta > 0:
                print("Next salat alarm in %d seconds" % delta)
        if delta <= 0:
            delta = stime-time.mktime(localtime())
            print("Next salat %s in %d seconds" % (SALATS[sidx], delta))
        
        
        # Setup wakeup button
        if delta > 24*3600: delta=24*3600
        wbuttons.setup_wakeup(wbutton)
        player.sleep()
        print("Calling : machine.deepsleep(%d)"%(delta*1000))
        machine.deepsleep(delta*1000)
    except Exception as err:
        led.value(1)
        with open('exception.log','w') as log:
            sys.print_exception(err,log)
            sys.print_exception(err)
        if raise_exceptions: raise

def _do_stop_adhan(_dumb):
    player.stop()
    time.sleep_ms(200) #To avoid disturbance of button click on wakeup
    sleepuntilnextsalat()
    # First initilization

pwm = None
_stopadhan=False
def irq_stop_adhan(pin):
    global _stopadhan
    _stopadhan = True
    micropython.schedule(_do_stop_adhan,0)

currvol=30
currsidx=None
VOL_STEP=1
VOL_STEP_MS=200

def _do_vol_up():
    global currvol, currsidx
    
    currvol=currvol+VOL_STEP
    
    if currvol > 30: currvol=30
    
    sdb.setsvolume(currsidx, currvol)
    player.volume(currvol)
    
    sdb.save()
    if volup.value() == 0:
        taskloop.sched_task(_do_vol_up, time.ticks_ms()+VOL_STEP_MS)
    
    
def _do_vol_dn():
    global currvol, currsidx
    
    currvol=currvol-VOL_STEP
    
    if currvol < VOL_STEP: currvol=VOL_STEP
    
    sdb.setsvolume(currsidx, currvol)
    player.volume(currvol)
    
    sdb.save()
    if voldn.value() == 0:
        taskloop.sched_task(_do_vol_dn, time.ticks_ms()+VOL_STEP_MS)

def irq_vol_control(pin):
    global currvol
    
    if pin == volup:
        op=_do_vol_up
    if pin == voldn:
        op=_do_vol_dn
    taskloop.sched_task(op)
    
def _setupvolcontrol(sidx=SPEECH_VOL_SIDX):
    global currvol, currsidx
    if volup:
        volup.irq(irq_vol_control, trigger=Pin.IRQ_FALLING)
    if voldn:
        voldn.irq(irq_vol_control, trigger=Pin.IRQ_FALLING)
    
    currsidx=sidx
    currvol=sdb.getsvolume(sidx)
    player.volume(currvol)


def alarm(sidx, salm):
    global _stopadhan
    _stopadhan=False
    player.wakeup()
    _setupvolcontrol(sidx)
    wbutton.irq(irq_stop_adhan, Pin.IRQ_FALLING)
    for i in range(1,5):
        led.value(1)
        time.sleep_ms(100)
        led.value(0)
        if _stopadhan: return
        time.sleep_ms(50)
    led.value(1)
    player.say_minutes_to_salat(sidx, salm) 
    
def adhan(sidx):
    global _stopadhan
    _stopadhan=False
    wbutton.irq(irq_stop_adhan, Pin.IRQ_FALLING)
    print('Adhan %s' % SALATS[sidx])
    led.value(1)
    
    if sidx == 1: #chorok : beep only
        _setupvolcontrol(sidx)
        player.say_salat_name(1)
        return
    
    urandom.seed(int(time.mktime(localtime())/60))
    # RNG needs some heat up to get a good enough quality
    for k in range(1,10): urandom.random()
    
    player.wakeup()
    _setupvolcontrol(sidx)
    if sidx == 0: #Fajr special ringing
        for i in range(1,17):
            led.value(1)
            time.sleep_ms(100)
            led.value(0)
            if _stopadhan: return
            time.sleep_ms(300 if i % 4 == 0 else 50)
        led.value(1)
        player.play_adhan(FAJR_ADHAN_FOLDER)
    else:
        for i in range(0, sidx):
            led.value(1)
            time.sleep_ms(100)
            led.value(0)
            if _stopadhan: return
            time.sleep_ms(500)
        led.value(1)
        _,_,_,h,mi,_,_,_ = localtime()
        player.say_current_time(h, mi)
        time.sleep_ms(500)
        player.play_adhan(ALL_ADHAN_FOLDER)
    
timer = machine.Timer(0)
def turnoff_wificonfig(timer):
    micropython.schedule(lambda x: sleepuntilnextsalat(False),0)

def match_time(tgttime, currtime):
    """ Check wether the given time is matched, taking into account BOOT_LATENCY
        If a match is found, the return will be delayed in order to ensure it will not match
        again
    """
    if tgttime <= currtime and (currtime - tgttime) < BOOT_LATENCY_SECS: 
        print("Time matching %d and %d" % (tgttime,currtime))
        time.sleep(BOOT_LATENCY_SECS-(currtime-tgttime))
        return True
    print("Time notmatching %d and %d" % (tgttime,currtime))
    return False
                

_last_btn_press = 0
def on_wifi_btn(pin):
    # End wificonfig session
    global _last_btn_press
    #DEbounce
    tick=time.ticks_ms() 
    if (tick - _last_btn_press) < 200: return
    _last_btn_press = tick
    timer.init(period=500, mode=machine.Timer.ONE_SHOT, callback=turnoff_wificonfig)

def sync_times_mawaqit():
    """ Supposes mawaqit.json exists with 'SSID','password','mcode','apikey' where 
    mcode = mosque UUID in mawaqit (obtained through search api).
    """
    import mawaqit
    mawaqit.dosync(sdb)

try:    
    if machine.wake_reason() == machine.EXT0_WAKE or sdb.isempty():
        if wbutton.value(): 
            #Button not pressed (0 = pressed !) : say time and exit
            led.value(1)
            time.sleep_ms(500)
            _,_,_,h,mi,_,_,_ = localtime()
            player.wakeup()
            _setupvolcontrol()
            print("Saying curren ttime")
            #Stop when clicking
            wbutton.irq(irq_stop_adhan, Pin.IRQ_FALLING)
            
            player.say_current_time(h, mi)
            
            if not sdb.isempty():
                sidx, stime = sdb.findnextsalat()
                print("Saying next salat at %r" % stime)
                _,_,_,h,mi,_,_,_ = time.localtime(stime)
                player.say_salat_at(sidx, h, mi)        
                
                sleepuntilnextsalat()
                #never reaches this line because of deep sleep
        # Config button still pressed or no salat times loaded
        led.value(1)
        import wificonfig
        PWM(led,1)
        wificonfig.start(sdb)
        wbutton.irq(on_wifi_btn, Pin.IRQ_FALLING)
        if sdb.isempty():
            print('Wifi config started, salat times empty')
        else:
            print('Wifi config will auto turnoff after 5 minutes')
            timer.init(period=5*60000, mode=machine.Timer.ONE_SHOT, callback=turnoff_wificonfig)
        player.wakeup()
        _setupvolcontrol()
        player.play_track(audioplayer.SPEECH_DATA_FOLDER,audioplayer.MSG_WIFI_SETUP, sync=False) #"Time now is"        
        taskloop.mainloop()
    else:
        #elif machine.wake_reason() == machine.TIMER_WAKE:
        #Verify adhan
        try:
            ntpsync()
        except:
            pass
        sidx, stime = sdb.findnextsalat()
        print("Next Salat is", sidx, stime)
        currtime = time.mktime(localtime())
        if match_time(stime,currtime):
            adhan(sidx)
        #IF alamr make alarm
        
        salm = sdb.getsalarmdelay(sidx)
        if salm != None:
            almtm = stime - (60 * salm)
            if match_time(almtm,currtime):
                alarm(sidx, salm)
        
        
        sleepuntilnextsalat() 
except Exception as err:
    led.value(1)
    with open('exception.log','w') as log:
        sys.print_exception(err,log)
        sys.print_exception(err)