import arch
#Turn on led asap
arch.LED_PIN.value(1)

import machine
import os
import sys
import utils

from machine import Pin, UART
import time
import micropython
from micropython import const
import esp32
from timesdb import SalatDB, SALATS, SPEECH_VOL_SIDX
from rtc import localtime, ntpsync
import urandom
import taskloop
import config


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

player = audioplayer.getplayer() 

FAJR_ADHAN_FOLDER=const(1)
ALL_ADHAN_FOLDER=const(2)

BOOT_LATENCY_SECS=const(30)

def setup_wakeup(pin_or_adc):
    if arch.ADC_KEYS_PIN:
        import wbuttons
        if isinstance(pin_or_adc, wbuttons.ADCButton):
            esp32.wake_on_ext0(Pin(arch.ADC_KEYS_PIN,Pin.IN,Pin.PULL_UP), esp32.WAKEUP_ALL_LOW)
            return
    if isinstance(pin_or_adc, Pin):
        esp32.wake_on_ext0(pin_or_adc, esp32.WAKEUP_ALL_LOW)
        return
    
    raise Exception("Unable to handle this type of buttons : %r" % pin_or_adc)


def led_on():
    if arch.LED_PIN:
        arch.LED_PIN.value(arch.LED_ON_VALUE)
        
def led_off():
    if arch.LED_PIN:
        arch.LED_PIN.value(not arch.LED_ON_VALUE)

def __next_salat_delta():
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
        
        if delta > 24*3600: delta=24*3600
        return delta
    
def sleepuntilnextsalat(raise_exceptions=True):
    """ returns idx when next salat time arrives """
    try:
        player.sleep()
        if config.get("alwaysAwake",True): #re read it live, in case config changes ...
            machine.deepsleep(1) #Reboot
        else:
            delta=__next_salat_delta()
            # Setup wakeup button
            setup_wakeup(wbutton)
            print("Calling : machine.deepsleep(%d)"%(delta*1000))
            machine.deepsleep(delta*1000+1)
    except Exception as err:
        led_on()
        with open('exception.log','w') as log:
            sys.print_exception(err,log)
            sys.print_exception(err)
        if raise_exceptions: raise

def _do_stop_adhan(_dumb):
    player.stop()
    time.sleep_ms(200) #To avoid disturbance of button click on wakeup
    sleepuntilnextsalat()
    # First initilization

_stopadhan=False
def irq_stop_adhan(pin):
    global _stopadhan
    _stopadhan = True
    micropython.schedule(_do_stop_adhan,0)

currvol=30
currsidx=None
VOL_STEP=5
VOL_STEP_MS=200

def _do_vol_up():
    global currvol, currsidx
    
    currvol=currvol+VOL_STEP
    
    if currvol > 30: currvol=30
    
    sdb.setsvolume(currsidx, currvol)
    player.volume(currvol)
    
    if volup.value() == 0:
        taskloop.sched_task(_do_vol_up, time.ticks_ms()+VOL_STEP_MS)
    else:
        sdb.save()

    
def _do_vol_dn():
    global currvol, currsidx
    
    currvol=currvol-VOL_STEP
    
    if currvol < VOL_STEP: currvol=VOL_STEP
    
    sdb.setsvolume(currsidx, currvol)
    player.volume(currvol)
    
    if voldn.value() == 0:
        taskloop.sched_task(_do_vol_dn, time.ticks_ms()+VOL_STEP_MS)
    else:
        sdb.save()

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
        led_on()
        time.sleep_ms(100)
        led_off()
        if _stopadhan: return
        time.sleep_ms(50)
    led_on()
    player.say_minutes_to_salat(sidx, salm) 
    
def adhan(sidx):
    global _stopadhan
    _stopadhan=False
    wbutton.irq(irq_stop_adhan, Pin.IRQ_FALLING)
    print('Adhan %s' % SALATS[sidx])
    led_on()
    
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
            led_on()
            time.sleep_ms(100)
            led_off()
            if _stopadhan: return
            time.sleep_ms(300 if i % 4 == 0 else 50)
        led_on()
        player.play_adhan(FAJR_ADHAN_FOLDER)
    else:
        for i in range(0, sidx):
            led_on()
            time.sleep_ms(100)
            led_off()
            if _stopadhan: return
            time.sleep_ms(500)
        led_on()
        _,_,_,h,mi,_,_,_ = localtime()
        player.say_current_time(h, mi)
        time.sleep_ms(500)
        player.play_adhan(ALL_ADHAN_FOLDER)
    
timer = machine.Timer(0)
def turnoff_wificonfig(timer):
    try:
        import autoupdater, wifi
        with wifi: 
            if autoupdater.download_updates():
                player.say_updating(True)
                autoupdater.deploy_updates()
                machine.deepsleep(1)
            else:
                player.say_no_update(True)
    except Exception as e:
        sys.print_exception(e)
        print("Update aborted due to exception")
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


STM_ADHAN=const(0)
STM_TIME=const(1)
STM_CONFIG=const(2)

LONGPRESS_DELAY_MS=500

startmode=None

try:
    if config.get("alwaysAwake",True):
        #TODO: here add breathing led tasks to taskloop
        led_off()
        nextsalat=time.ticks_ms()+__next_salat_delta()*1000 
        if wbutton.value() == 0:  
            #Wbutton pressed at startup => Config mode
            startmode=STM_CONFIG
        else:
            #Wait for button press or next salat
            wbutton.irq(lambda pin: taskloop.stoploop())
            taskloop.mainloop(until_ms=nextsalat)
            led_on()
            wbutton.irq(None)
            if time.ticks_ms() > nextsalat:
                startmode=STM_ADHAN
            else:
                time.sleep_ms(LONGPRESS_DELAY_MS)
                if wbutton.value() == 0:
                    startmode=STM_CONFIG
                else:
                    startmode=STM_TIME
    else:
        if machine.wake_reason() == machine.EXT0_WAKE or sdb.isempty():
            if wbutton.value(): 
                startmode=STM_TIME
            else:
                startmode=STM_CONFIG
        else:
            startmode=STM_ADHAN
    
    if startmode==STM_TIME:
        #Button not pressed (0 = pressed !) : say time and exit
        led_on()
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
            time.sleep_ms(1000)
            player.say_random_reminder()
            
            sleepuntilnextsalat()
        else:
            startmode=STM_CONFIG
            
    if startmode==STM_CONFIG:
        # Config button still pressed or no salat times loaded
        led_on()
        import wificonfig
        wificonfig.start(sdb, player)
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
    
    if startmode==STM_ADHAN:
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
    led_on()
    with open('exception.log','w') as log:
        sys.print_exception(err,log)
        sys.print_exception(err)
