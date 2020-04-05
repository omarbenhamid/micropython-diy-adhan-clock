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

c = config.get("wifi")
SSID = c['SSID']
password = c['password']

def __enter__():
    global SSID, password
    if not conn.isconnected() or not conn.active():
        conn.active(True)
        conn.disconnect()
        conn.connect(SSID,password)
        s=time.ticks_ms()
        while not conn.isconnected() and ((time.ticks_ms() - s) < WIFI_CONN_TIMEOUT_MS):
            time.sleep_ms(500)

    if not conn.isconnected():
        raise Exception("Cannot connect to wifi")


def __exit__(*exc_info):
    if conn.isconnected():
        conn.disconnect()
    conn.active(False)
