'''
Created on 29 sept. 2019

@author: omar
'''
import time
import urandom
import re
import os

from machine import Pin
from micropython import const
import audio
import taskloop

def tohexstring(bytes):
    return " ".join('%X' % b for b in bytes)
    
    
HOURS_TRACKS_FIRST=const(200)
MINUTES_TRACKS_FIRST=const(100)

SALAT_NAMES_TRACKS_FIRST=const(20)
MSG_TIME_IS_NOW=const(1)
MSG_WIFI_SETUP=const(2)
MSG_AT=const(3)

SPEECH_DATA_FOLDER=3

REMINDERS_FOLDER=4

AUDIO_DIR_FMT="/sdcard/audiodata/%(folder)02d"
AUDIO_URI_FMT="file:/"+AUDIO_DIR_FMT+"/%(track)03d"
AUDIO_SUPPORTED_EXTS=[".wav",".mp3",".ogg",".amr"]

AUDIO_MAX_VOLUME=80

def exists(folder, track, ext):
    fname="%03d%s" % (track, ext)
    return fname in os.listdir(AUDIO_DIR_FMT%{"folder":folder})

class AudioPlayer:
    def __init__(self, ignoreerrors=False):
        """ Initialize with an instance of machine.UART where YX5300 is wired
        speaker_pin parameter is the pin where speeker is has VCC to turnit on/off at will
        sleep when True (default) the device is put to sleep else it is woken up"""
        self.player = audio.player(None)
        self.ignoreerrors=ignoreerrors
        
    def play_track(self, folder=None, track=None, sync=False):
        """ Play given track of given folder, if no folder/track is provided : "next track is played" 
        if waitmillis is set the function blocks until either *playing finishes" or the value waitmillis is reached (put a big value to wait "undefenitely") 
           if timeout is reached an exception is raised.
        """
        print("play track")
        assert(folder != None or track != None)
        pfx=AUDIO_URI_FMT % {"track":track, "folder":folder}
        uri=None
        for ext in AUDIO_SUPPORTED_EXTS:
            if exists(folder, track, ext):
                uri=pfx+ext
                break
        if uri == None:
            if self.ignoreerrors: return
            else: raise Exception("No such track folder %d track %d" % (folder,track))
            
        print("playing uri %s , sync=%r" % (uri, sync))
        self.player.play(uri)
        if sync:
            taskloop.mainloop(self.isstopped)
            
        
    def stop(self):
        self.player.stop()
    
    def volume(self, level):
        """ Level from 0 To 30 """
        self.player.vol(level*AUDIO_MAX_VOLUME//30)
    
    def sleep(self):
        pass
    
    def wakeup(self):
        pass
    
    def query_track_count(self, folder):
        try:
            f=list(int(f[:-4]) for f in os.listdir(AUDIO_DIR_FMT % {"folder":folder}) 
               if f[-4:] in AUDIO_SUPPORTED_EXTS and len(f) == 7 \
                    and re.match('^[0-9]+$',f[:-4]))
            return max(f) if f else 0
        except OSError:
            return 0
        
    def say_time(self, hours, minutes):
        if not SPEECH_DATA_FOLDER: 
            print("No speech data folder defined, not speeking ...")
            return 
        self.play_track(SPEECH_DATA_FOLDER, HOURS_TRACKS_FIRST+hours, sync=True)
        self.play_track(SPEECH_DATA_FOLDER, MINUTES_TRACKS_FIRST+minutes, sync=True)
    
    def say_current_time(self, hours, minutes):
        self.play_track(SPEECH_DATA_FOLDER,MSG_TIME_IS_NOW, sync=True) #"Time now is"        
        self.say_time(hours, minutes)
        
    def say_salat_at(self, sidx, hours, minutes):
        self.play_track(SPEECH_DATA_FOLDER, SALAT_NAMES_TRACKS_FIRST+sidx, sync=True)
        self.play_track(SPEECH_DATA_FOLDER, MSG_AT, sync=True)
        self.say_time(hours, minutes)
    
    def say_salat_name(self, sidx):
        self.play_track(SPEECH_DATA_FOLDER, SALAT_NAMES_TRACKS_FIRST+sidx, sync=True)
        
    def say_minutes_to_salat(self, sidx, salm):
        self.play_track(SPEECH_DATA_FOLDER, SALAT_NAMES_TRACKS_FIRST+sidx, sync=True)
        self.play_track(SPEECH_DATA_FOLDER, MINUTES_TRACKS_FIRST+salm, sync=True)
        
    def say_random_reminder(self):
        if not REMINDERS_FOLDER: return
        cnt=self.query_track_count(REMINDERS_FOLDER)
        if cnt == 0: return
        self.play_track(REMINDERS_FOLDER, urandom.randrange(1,cnt+1), 
                        sync=True)
        
        
    def play_adhan(self, folder):
        self.play_track(folder, urandom.randrange(1,self.query_track_count(folder)+1), 
                        sync=True)
    
    def isrunning(self):
        return self.player.get_state()["status"] == audio.player.STATUS_RUNNING
    
    def isstopped(self):
        return self.player.get_state()["status"] != audio.player.STATUS_RUNNING
    