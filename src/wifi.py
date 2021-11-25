"""
    Usage :
    import wifi
    with wifi:
        ... do stuff that requires connection ...

    Reads wifi config from config.json :
    {
        ...
        "wifi": {
            "SSID":"XXXXX",
            "password":"XXXXX"
        },
        ...
    }
"""

import config
import network
import time
import smartconfig
import taskloop
import micropython

WIFI_CONN_TIMEOUT_MS=30*1000

conn = network.WLAN(network.STA_IF)

def say_wifi_ko_safe():
    try:
        import arch
        if arch.AUDIO_PLAYER_UART:
            import yx5300_audioplayer as audioplayer
        else:
            import adf_audioplayer as audioplayer
        audioplayer.getplayer().say_wifi_ko(sync=True)
    except:
        pass
    
def say_reconfigured_safe():
    try:
        import arch
        if arch.AUDIO_PLAYER_UART:
            import yx5300_audioplayer as audioplayer
        else:
            import adf_audioplayer as audioplayer
        audioplayer.getplayer().say_wifi_ko(sync=True)
    except:
        pass
    

def connect(SSID=None, password=None, timeoutmillis=None, voice_feedback=True):
    """
        Connect to given or configured wifi.
        If timeoutmillis is not set: retunr immediately
    """
    if SSID==None and password==None:
        c = config.get("wifi")
        if c==None: raise Exception("Wifi not configured")
        SSID = c.get('SSID')
        if not SSID: raise Exception("Wifi not configured properly")
        password = c.get('password','')
        
        
    if not conn.isconnected() or not conn.active():
        conn.active(True)
        conn.disconnect()
        conn.connect(SSID,password)
        
        if timeoutmillis == None:
            return #Don't wait
        
        taskloop.mainloop(lambda: conn.isconnected(), 
                          until_ms=time.ticks_ms()+timeoutmillis )
        
        
    if not conn.isconnected():
        start_smartconfig()
        if voice_feedback: say_wifi_ko_safe()
        raise Exception("Cannot connect to wifi")

def disconnect():
    if conn.isconnected():
        conn.disconnect()
    conn.active(False)

def __enter__():
    connect(timeoutmillis=WIFI_CONN_TIMEOUT_MS)


def __exit__(*exc_info):
    disconnect()

def __verify_and_save_smartconfig(conf):
    ssid,pwd=conf
    try:
        conn.disconnect()
        conn.active(False)
        connect(SSID=ssid, password=pwd, voice_feedback=False, timeoutmillis=WIFI_CONN_TIMEOUT_MS)
    except Exception as e:
        print("Smartconfig credentials test failed, starting over")
        say_wifi_ko_safe() #TODO: use a specific message ?
        start_smartconfig()
        sys.print_exception(e)
        return
    config.set("wifi.SSID", ssid)
    config.set("wifi.password", pwd)
    config.save()
    say_reconfigured_safe()
    

def __check_smartconfig_status():
    #if smartconfig.status() != smartconfig.SC_STATUS_LINK_OVER: return
    if smartconfig.status() not in \
        (smartconfig.SC_STATUS_LINK_OVER, smartconfig.SC_STATUS_LINK): 
        return
    
    print("Received smartconfig wifi configuration")
    stop_smartconfig()
    micropython.schedule(__verify_and_save_smartconfig, 
                         (smartconfig.get_ssid(), 
                          smartconfig.get_password()) )
    
    
def start_smartconfig():
    conn.active(True)
    
    smartconfig.set_type(smartconfig.ESPTOUCH)
    smartconfig.start()
    
    taskloop.sched_task(__check_smartconfig_status, repeat_ms=500)
    
    print("Started smartconfig listener in taskloop")
    
def stop_smartconfig():
    smartconfig.stop()
    #Don desactivet the connection so that not to interfer.
    taskloop.unsched_task(__check_smartconfig_status)