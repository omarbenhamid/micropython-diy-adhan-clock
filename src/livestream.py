'''
Created on Oct 28, 2021

@author: omar
'''
import ussl, usocket, sys, time
import taskloop
import audio
from micropython import const


from _thread import start_new_thread

LS_POLL_DELAY_MIN_MS=30000

LS_POLL_DELAY_MAX_MS=120000

LS_CB_TRIGGER_DELAY_MS=1000

def _head_status(url):
    proto, dummy, host, path = url.split("/", 3)
    port= 443 if proto == "https:" else 80
    if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)
    
    ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
    #print(ai)
    ai=ai[0]
    s = usocket.socket(ai[0], ai[1], ai[2])
    s.connect(ai[-1])
    try:
        if proto == "https:":
            s = ussl.wrap_socket(s)
        
        s.write("\r\n".join(
        ("HEAD /%s HTTP/1.0" % path,
         "Host: %s" % host,
          "\r\n"
         )
        ))
    
        l=s.readline()
    
        status = int(l.split(None, 2)[1])
    
        while l.strip():
            l=s.readline()
        return status
    finally:
        s.close()


class LiveStream():
    def __init__(self, stream_url, status_callback=None, adf_player=None, ignore_errors=False):
        """
            stream_url : mp3 url
            status_callback: callback function called when availability status changed.
            adf_player: audio.player object if not set a new one is created
        
            After call of watch(...)
            The stream will be polled with random delay between LS_POLL_DELAY_MIN_MS
            and LS_POLL_DELAY_MAX_MS with a HEAD request. The eventual passed callback
            will be invoked with the status (True if available of False if note) when
            the status of the livestream changes.
        """
        self.player = adf_player or audio.player(None)
        self.stream_url=stream_url
        self.ignore_errors=ignore_errors
        
        self.status_callback=status_callback
        
        self.last_status=None
        self.stream_status=False
        self.watching=False
        self.watchuntil=None
        
    def watch(self, watch_duration_ms=None, status_callback=None):
        """ Start backend thread to check the stream status 
        if watch_duration_ms is specified, watching stops after that delay"""
        self.watchuntil=None if not watch_duration_ms else time.ticks_ms()+watch_duration_ms
        if status_callback:
            self.status_callback=status_callback
        
        if self.watching: 
            return #Already watching

        self.watching=True
        start_new_thread(self._poll_update_status, [])
        if self.status_callback:
            taskloop.sched_task(self.trigger_stream_cb, 
                                   repeat_ms=LS_CB_TRIGGER_DELAY_MS)
        
    def stop_watching(self):
        """ Stops watching session """
        self.watching=False
        taskloop.unsched_task(self.__trigger_stream_cb)
    
    def check_status_sync(self):
        try:
            s=_head_status(self.stream_url)
            self.stream_status = (s >= 200 and s <= 299)
        except Exception as err:
            self.stream_status=False
            sys.print_exception(err)
        return self.stream_status
    
   
    def playnow(self, force=False):
        """ 
            If force = True: no check is performed : stream is played.
            Else, play the stream if available
            
            return True if stream has been played
            return False if stream not available.
        """
        if force or self.stream_status:
            self.player.play(self.stream_url)
            return True
        return False
    
    def stop(self):
        self.player.stop()
    
    def isplaying(self):
        return self.player.get_state()["status"] == audio.player.STATUS_RUNNING
    
    def _poll_update_status(self):
        try:
            while self.watching:
                if self.watchinguntil and time.ticks_ms() >= self.watchinguntil:
                    break
                
                self.check_status_sync(self)
                
                eticks=time.ticks_ms()
                if self.watchinguntil and eticks >= self.watchinguntil:
                    break
                
                w=urandom.randrange(LS_POLL_DELAY_MIN_MS, LS_POLL_DELAY_MAX_MS)
                if self.watchuntil:
                    w=max(min(w, self.watchuntil-eticks),LS_POLL_DELAY_MIN_MS)
                    
                time.sleep_ms(w)
        finally:
            self.stop_watching()
    
    def __trigger_stream_cb(self):
        stat=self.stream_status
        if stat == self.last_status: return
        self.last_status=stat
        if self.status_callback: self.status_callback(stat)
        
        
in main do 
if config.get(liveStreamUrl) :
    live=LiveStream(...)
    => In adhat, wait 30s :
    if live.check_status_sync() => live.playnow()
    else, after adhan
    live.watch(5 minutes) #A khotba might start in 5minutes max.
    
            