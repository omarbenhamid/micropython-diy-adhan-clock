'''
Created on Oct 28, 2021

@author: omar
'''
import ussl, usocket, sys, time
import taskloop
import audio
from micropython import const


from _thread import start_new_thread

LS_POLL_DELAY_MS=60000
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
        """
        self.player = adf_player or audio.player(None)
        self.stream_url=stream_url
        self.ignore_errors=ignore_errors
        self.status_callback=status_callback
        self.last_status=None
        self.stream_status=False
        
        self.watching=True
        
        start_new_thread(self._poll_update_status, [])
                         
        taskloop.sched_task(self.trigger_stream_cb, 
                               repeat_ms=LS_CB_TRIGGER_DELAY_MS)
        
    def destroy(self):
        self.watching=False
        taskloop.unsched_task(self.trigger_stream_cb)
    
    def _poll_update_status(self):
        while self.watching:
            try:
                s=_head_status(self.stream_url)
                self.stream_status = (s >= 200 and s <= 299)
            except Exception as err:
                self.stream_status=False
                sys.print_exception(err)
            time.sleep_ms(LS_POLL_DELAY_MS)
                
    
    def set_status_callback(self, status_callback):
        self.status_callback=status_callback
    
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
    
    def trigger_stream_cb(self):
        stat=self.stream_status
        if stat == self.last_status: return
        self.last_status=stat
        if self.status_callback: self.status_callback(stat)
            