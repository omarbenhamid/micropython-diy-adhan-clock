'''
Created on 29 sept. 2019

@author: omar
'''
import yx5300
import time
import urandom

from machine import Pin
from micropython import const

def tohexstring(bytes):
    return " ".join('%X' % b for b in bytes)
    
    
HOURS_TRACKS_FIRST=const(200)
MINUTES_TRACKS_FIRST=const(100)

SPEECH_DATA_FOLDER=3

SALAT_NAMES_TRACKS_FIRST=const(20)
MSG_TIME_IS_NOW=const(1)
MSG_WIFI_SETUP=const(2)
MSG_AT=const(3)

MIN_ADHAN_COUNT=const(5) #Number of adhans to consider is query fails.
ADHAN_TIMEOUT=const(300000)
SAY_HOUR_TIMEOUT=const(2500)
SAY_AND_TIMEOUT=const(1000)
SAY_MIN_TIMEOUT=const(3000)
SAY_AT_TIMEOUT=const(2000)
SAY_SALAT_NAME_TIMEOUT=const(3500)
SAY_TIME_IS_NOW_TIMEOUT=const(1500)

class AudioPlayer:
    def __init__(self, uart, speaker_pin = None, sleep=True, speech_data_folder=None, ignoreerrors=False):
        """ Initialize with an instance of machine.UART where YX5300 is wired
        speaker_pin parameter is the pin where speeker is has VCC to turnit on/off at will
        sleep when True (default) the device is put to sleep else it is woken up"""
        self.player = uart
        self.spk = speaker_pin
        if self.spk: self.spk.init(Pin.OUT, Pin.PULL_DOWN)
        self.speech_data_folder = speech_data_folder
        self.ignoreerrors=ignoreerrors
        if sleep: self.sleep()
        else: self.wakeup()
        self.pendingtask=None #This is a method called as soon as possible.
        self.pttime=0 #Time to execute the task
    def sched_task(self,taskfn, exectime_ms=0):
        """ Call the given callable when waiting read:
        taskfn will be called.
        if exectime_ms is set, it will run when time.ticks_ms() reaches this value.
        This is mainly here to be able to handle irqs while reading ...
        """
        self.pendingtask=taskfn
        self.pttime=exectime_ms
        
    def play_track(self, folder=None, track=None, waitmillis=0):
        """ Play given track of given folder, if no folder/track is provided : "next track is played" 
        if waitmillis is set the function blocks until either *playing finishes" or the value waitmillis is reached (put a big value to wait "undefenitely") 
           if timeout is reached an exception is raised.
        """
        
        self._flush_uart_buffer()
        
        if folder == None or track == None:
            self.player.write(yx5300.play_next())
        elif track < 0:
            return
        else:
            self.player.write(yx5300.play_track(track, folder))
        if waitmillis == 0: return
        try:
            self.wait_for_response(0x3D, time.ticks_ms() + waitmillis)
        except:
            if self.ignoreerrors: return
            else: raise
        
    def stop(self):
        self.player.write(yx5300.stop())
    
    def volume(self, level):
        """ Level from 0 To 30 """
        self.player.write(yx5300.set_volume(level))
    
    def sleep(self):
        self.player.write(yx5300.sleep_module())
        if self.spk: self.spk.value(0) #Turn off speaker
        
    def wakeup(self):
        self.player.write(yx5300.wake_module())
        time.sleep_ms(200)
        if self.spk: self.spk.value(1) #Turn on speaker
    
    def _flush_uart_buffer(self):
        while self.player.read():
            pass
    
    def _perform_pending(self):
        if self.pendingtask and self.pttime <= time.ticks_ms():
            task=self.pendingtask
            self.pendingtask=None
            task()
            return True
        return False
    
    def _timeout_read(self,maxtime):
        try:
            ret = self.player.read(1)
            
            while not ret:
                if time.ticks_ms() > maxtime:
                    raise Exception("Timeout reading input")
                if not self._perform_pending():
                    time.sleep_ms(50)
                ret = self.player.read(1)
                
            return ret[0]
        finally:
            self._perform_pending()
    
    def _read_response(self, maxtime):
        c = self._timeout_read(maxtime)
        if c != 0x7E: raise Exception("Unexpected header [0] 0x%x : 0x7E expected" % c )
        c = self._timeout_read(maxtime)
        if c != 0xFF: raise Exception("Unexpected header [1] 0x%x : 0xFF expected" % c)
        c = self._timeout_read(maxtime)
        ret = bytearray(c)
        for i in range(0,c):
            ret[i] = self._timeout_read(maxtime)
        c = self._timeout_read(maxtime)
        if c != 0xEF: raise Exception("Unexpected tail 0x%x : 0xEF expected" % c)
        
        return ret
    
    def wait_for_response(self, code, maxtime, ignore_errors=False):
        """ Waits for a response with given code (ignoring all other resposnes), raises exception when time.ticks_ms() reaches maxtime """
        ret = self._read_response(maxtime)
        crit = (code,) if ignore_errors else (code, 0x40)
        
        while ret[0] not in crit and (time.ticks_ms() < maxtime):
            print('Ignored response %s' % tohexstring(ret))
            ret = self._read_response(maxtime)
            
        if not ignore_errors and ret[0] == 0x40:
            raise Exception("Error received from device : %s" % tohexstring(ret))
        
        if ret[0] == code: return ret
        
        raise Exception("Timeout waiting for response with code %X, last received : %s" % (code,tohexstring(ret)))
            
    def query(self,queryCmd, DL=0x00):
        cmd = yx5300.command_base()
        cmd[3] = queryCmd
        cmd[6] = DL
        # Flush buffer
        self._flush_uart_buffer()
        self.player.write(cmd)
        
        return self._read_response(time.ticks_ms() + 500)

    def query_track_count(self, folder):
        try:
            ret = self.query(0x4E,DL=folder)
            if ret[0] != 0x4E: raise Exception("Error querying track count for folder %d, response : %s" % (folder,tohexstring(ret)))
            return ret[3]
        except:
            if self.ignoreerrors: return MIN_ADHAN_COUNT
            else: raise
        
    def query_playback_status(self):
        ret = self.query(0x42)
        if ret[0] != 0x42: raise Exception("Error querying playback status, response : %s" % tohexstring(ret))
        return ret[3]
    
    def say_time(self, hours, minutes):
        if not self.speech_data_folder: 
            print("No speech data folder defined, not speeking ...")
            return 
        self.play_track(self.speech_data_folder, HOURS_TRACKS_FIRST+hours, waitmillis=SAY_HOUR_TIMEOUT)
        self.play_track(self.speech_data_folder, MINUTES_TRACKS_FIRST+minutes, waitmillis=SAY_MIN_TIMEOUT)
    
    def say_current_time(self, hours, minutes):
        self.play_track(self.speech_data_folder,MSG_TIME_IS_NOW, waitmillis=SAY_TIME_IS_NOW_TIMEOUT) #"Time now is"        
        self.say_time(hours, minutes)
        
    def say_salat_at(self, sidx, hours, minutes):
        if not self.speech_data_folder: 
            print("No speech data folder defined, not speeking ...")
            return 
        self.play_track(self.speech_data_folder, SALAT_NAMES_TRACKS_FIRST+sidx, waitmillis=SAY_SALAT_NAME_TIMEOUT)
        self.play_track(self.speech_data_folder, MSG_AT, waitmillis=SAY_AT_TIMEOUT)
        self.say_time(hours, minutes)
    
    def say_salat_name(self, sidx):
        self.play_track(self.speech_data_folder, SALAT_NAMES_TRACKS_FIRST+sidx, waitmillis=SAY_SALAT_NAME_TIMEOUT)
        
    def say_minutes_to_salat(self, sidx, salm):
        if not self.speech_data_folder: 
            print("No speech data folder defined, not speeking ...")
            return 
        self.play_track(self.speech_data_folder, SALAT_NAMES_TRACKS_FIRST+sidx, waitmillis=SAY_SALAT_NAME_TIMEOUT)
        self.play_track(self.speech_data_folder, MINUTES_TRACKS_FIRST+salm, waitmillis=SAY_MIN_TIMEOUT)
        
    def play_adhan(self, folder):
        self.play_track(folder, urandom.randrange(1,self.query_track_count(folder)+1), waitmillis=ADHAN_TIMEOUT)
        