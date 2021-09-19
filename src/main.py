import machine
from machine import Pin, PWM, UART
import yx5300
import time
import micropython
from micropython import const
import esp32
from timesdb import SalatDB, SALATS
from rtc import localtime, ntpsync
import urandom
import sys
import audio
import arch
from arch import VOL_DN_PIN

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
wbutton = Pin(arch.WBUTTON_PIN,Pin.IN,Pin.PULL_UP)
if arch.VOL_UP_PIN and arch.VOL_DN_PIN:
    volup=Pin(arch.VOL_UP_PIN,Pin.IN,Pin.PULL_UP)
    voldn=Pin(arch.VOL_DN_PIN,Pin.IN,Pin.PULL_UP)
else:
    volup=vodnpin=None

led=Pin(arch.LED_PIN, Pin.OUT)
speaker_vcc = None if arch.SPEAKER_PIN==None else Pin(arch.SPEAKER_PIN)

player = audio.AudioPlayer(UART(arch.AUDIO_PLAYER_UART,9600), speaker_pin=speaker_vcc, speech_data_folder=3, ignoreerrors=True)

FAJR_ADHAN_FOLDER=const(1)
ALL_ADHAN_FOLDER=const(2)

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
        esp32.wake_on_ext0(wbutton, esp32.WAKEUP_ALL_LOW)
        player.sleep()
        machine.deepsleep(delta*1000)
    except Exception as err:
        led.value(1)
        play_tone(100, 5000)
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

def _do_update_volume(_dumb=None):
    global currvol, currsidx

    sdb.setsvolume(currsidx, currvol)
    player.volume(currvol)


def irq_vol_control(pin):
    global currvol
    if pin == volup:
        currvol += VOL_STEP
        if currvol > 30: currvol=30
    if pin == voldn:
        currvol -= VOL_STEP
        if currvol < 0: currvol=0
    if player.busy():
        player.do_task_asap(_do_update_volume)
    else:
        micropython.schedule(_do_update_volume,0)

def _setupvolcontrol(sidx):
    global currvol, currsidx
    if volup:
        volup.irq(irq_vol_control)
    if voldn:
        voldn.irq(irq_vol_control)
    
    currsidx=sidx
    currvol=sdb.getsvolume(sidx)
    player.volume(currvol)


def alarm(sidx, salm):
    global _stopadhan
    _stopadhan=False
    player.wakeup()
    _setupvolcontrol(sidx)
    wbutton.irq(irq_stop_adhan, Pin.IRQ_FALLING,machine.SLEEP|machine.DEEPSLEEP)
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
    wbutton.irq(irq_stop_adhan, Pin.IRQ_FALLING,machine.SLEEP|machine.DEEPSLEEP)
    print('Adhan %s' % SALATS[sidx])
    led.value(1)
    
    if sidx == 1: #chorok : beep only
        player.volume(30)
        player.say_salat_name(1)
        return
    
    urandom.seed(time.mktime(localtime()))
    # RNG needs some heetup to get a good enough quality
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
        if not wbutton.value(): #Button still pressed (0 = pressed !)
            led.value(1)
            time.sleep_ms(500)
            _,_,_,h,mi,_,_,_ = localtime()
            player.wakeup()
            player.volume(30)
            print("Saying curren ttime")
            player.say_current_time(h, mi)
            
            sidx, stime = sdb.findnextsalat()
            print("Saying next salat at %r" % stime)
            _,_,_,h,mi,_,_,_ = time.localtime(stime)
            player.say_salat_at(sidx, h, mi)        
            
            sleepuntilnextsalat()
            #never reaches this line because of deep sleep
        else:
            # Config button prcessed or no salat times loaded
            led.value(1)
            import wificonfig
            PWM(led,1)
            wificonfig.start(sdb)
            wbutton.irq(on_wifi_btn, Pin.IRQ_FALLING,machine.SLEEP|machine.DEEPSLEEP)
            if sdb.isempty():
                print('Wifi config started, salat times empty')
            else:
                print('Wifi config will auto turnoff after 5 minutes')
                timer.init(period=5*60000, mode=machine.Timer.ONE_SHOT, callback=turnoff_wificonfig)
            player.wakeup()
            player.volume(30)
            player.play_track(player.speech_data_folder,audio.MSG_WIFI_SETUP) #"Time now is"        
            
    else:
        #elif machine.wake_reason() == machine.TIMER_WAKE:
        try:
            ntpsync()
        except:
            pass
        sidx, stime = sdb.findnextsalat()
        print("Next Salat is", sidx, stime)
        currtime = time.mktime(localtime())
        if stime <= currtime and (currtime - stime) < 10:
            adhan(sidx)
        #IF alamr make alarm
        
        salm = sdb.getsalarmdelay(sidx)
        if salm != None:
            almtm = stime - (60 * salm)
            if almtm <= currtime and (currtime - almtm) < 10: 
                alarm(sidx, salm)
        
        
        sleepuntilnextsalat() 
except Exception as err:
    led.value(1)
    with open('exception.log','w') as log:
        sys.print_exception(err,log)
        sys.print_exception(err)