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
    

def connect(SSID=None, password=None, timeoutmillis=None):
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
        s=time.ticks_ms()
        if timeoutmillis == None:
            return #Don't wait
        while not conn.isconnected() and ((time.ticks_ms() - s) < timeoutmillis):
            time.sleep_ms(500)
    

    if not conn.isconnected():
        conn.active(False) #disable connection
        say_wifi_ko_safe()
        raise Exception("Cannot connect to wifi")

def disconnect():
    if conn.isconnected():
        conn.disconnect()
    conn.active(False)

def __enter__():
    connect(timeoutmillis=WIFI_CONN_TIMEOUT_MS)


def __exit__(*exc_info):
    disconnect()
