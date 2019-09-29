'''
Created on 29 sept. 2019

@author: omar
'''
import yx5300
import time
from machine import Pin

def tohexstring(bytes):
    return " ".join('%X' % b for b in bytes)
    

class AudioPlayer:
    def __init__(self, uart, speaker_pin = None, sleep=True):
        """ Initialize with an instance of machine.UART where YX5300 is wired
        speaker_pin parameter is the pin where speeker is has VCC to turnit on/off at will
        sleep when True (default) the device is put to sleep else it is woken up"""
        self.player = uart
        self.spk = speaker_pin
        self.spk.init(Pin.OUT, Pin.PULL_DOWN)
        if sleep: self.sleep()
        else: self.wakeup()
    
    def play_track(self, folder=None, track=None, waitmillis=0, pollstatusmillis=500):
        """ Play given track of given folder, if no folder/track is provided : "next track is played" 
        if waitmillis is set the function blocks until either *playing finishes" or the value waitmillis is reached (put a big value to wait "undefenitely") 
           you can use query_playback_status to check if playback is finished or not yet after wait timeout.
         
        poll status millis : the number of milliseconds to check if track finished : the higher it is the less frequently the player is polled for playback status
        """
        
        if folder == None or track == None:
            self.player.write(yx5300.play_next())
        else:
            self.player.write(yx5300.play_track(track, folder))
        if waitmillis == 0: return
        
        timeout = time.ticks_ms() + waitmillis #Max 5 minutes
        time.sleep_ms(200)
        while self.query_playback_status() != 0x01 and (time.ticks_ms() < timeout): #Waiting for playing to start (0x01 see to YX5300 datasheet)
            time.sleep_ms(200)
        while self.query_playback_status() == 0x01 and (time.ticks_ms() < timeout): #playing state according to YX5300 datasheet
            time.sleep_ms(pollstatusmillis)
        
        
    def stop(self):
        self.player.write(yx5300.stop())
    
    def volume(self, level):
        """ Level from 0 To 30 """
        self.player.write(yx5300.set_volume(level))
    
    def sleep(self):
        self.player.write(yx5300.sleep_module())
        if self.spk: self.spk.value(0) #Turn on speaker
        
    def wakeup(self):
        self.player.write(yx5300.wake_module())
        time.sleep_ms(200)
        if self.spk: self.spk.value(1) #Turn on speaker
    
    def _timeout_read(self,maxtime):
        ret = self.player.read(1)
        
        while not ret:
            if time.ticks_ms() > maxtime:
                raise Excepton("Timeout reading input")
            time.sleep_ms(100)
            ret = self.player.read(1)
            
        return ret[0]
    
            
    def query(self,queryCmd, DL=0x00):
        cmd = yx5300.command_base()
        cmd[3] = queryCmd
        cmd[6] = DL
        # Flush buffer
        while self.player.read():
            pass
        self.player.write(cmd)
        
        maxtime = time.ticks_ms() + 1000 # Timeout after one second
        
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
    

    def query_track_count(self, folder):
        ret = self.query(0x4E,DL=folder)
        if ret[0] != 0x4E: raise Exception("Error querying track count for folder %d, response : %s" % (folder,tohexstring(ret)))
        return ret[3]
    
    def query_playback_status(self):
        ret = self.query(0x42)
        if ret[0] != 0x42: raise Exception("Error querying playback status, response : %s" % tohexstring(ret))
        return ret[3]
    