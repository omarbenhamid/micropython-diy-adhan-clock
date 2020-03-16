import time
import json
import network
import urequests
import naya
import io
import gc

WIFI_CONN_TIMEOUT_MS=30*1000

conn = network.WLAN(network.STA_IF)

def _iter_months(token_stream, sdb):
    for t,n in token_stream:
        if n != "calendar": continue
        t,n = next(token_stream)
        if n != ':': continue
        break
    assert(next(token_stream)==(0,'['))
    tok = (0,',')
    mnum = 0
    while tok == (0,','):
        mnum = mnum + 1
        gc.collect()
        sdb.import_mawaqit_month_stream(mnum, token_stream)
        tok =  next(token_stream)
    
def downloadtimes(SSID, password, apikey, mcode, sdb):
    if not conn.isconnected() or not conn.active():
        conn.active(True)
        conn.disconnect()    
        conn.connect(SSID,password)
        s=time.ticks_ms()
        while not conn.isconnected() and ((time.ticks_ms() - s) < WIFI_CONN_TIMEOUT_MS):
            time.sleep_ms(500)
        
    if not conn.isconnected():
        raise Exception("Cannot connect to wifi")

    try:
        r=urequests.get('https://mawaqit.net/api/2.0/mosque/%s/prayer-times?calendar=yes' % mcode,
                  headers={"accept": "application/json","Api-Access-Token":apikey})
        
        if sdb == None: return r.content
        sdb.resetdb()
        _iter_months(naya.tokenize(r.raw), sdb)
        return None
    finally:
        conn.disconnect()

def dosync(sdb):
    with open("mawaqit.json","r") as f:
        data = json.load(f)
    return downloadtimes(sdb=sdb,**data)

