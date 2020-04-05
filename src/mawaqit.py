import time
import json
import urequests
import naya
import io
import gc
import wifi
import config


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
    
def downloadtimes(apikey, uuidMosquee, sdb):
    with wifi:
        r=urequests.get('https://mawaqit.net/api/2.0/mosque/%s/prayer-times?calendar=yes' % uuidMosquee,
                  headers={"accept": "application/json","Api-Access-Token":apikey})
        
        if sdb == None: return r.content
        sdb.resetdb()
        _iter_months(naya.tokenize(r.raw), sdb)
        return None
    

def dosync(sdb):
    return downloadtimes(sdb=sdb,**(config.get("mawaqit")))

