import json
import sys
import utils
import os

CONFIG_LOC="/config.json"
CONFIG_SDCARD_UPDATE='/sdcard/config.json'

config={}

if not utils.path_exists(CONFIG_LOC):
    print("config.json not found, writing minimum config")
    with open(CONFIG_LOC,'w') as f:
        json.dump({
            "rtc": {
                "ntphost": "pool.ntp.org",
                "timezoneDeltaMinutes": 120,
                "DS1302": False
            }
        }, f)

def reload():
    global config
    try:
        with open(CONFIG_LOC,'r') as f:
            config = json.load(f)
    except Exception as err:
        config = {}
        sys.print_exception(err)
        print("Failed to load %s, ignored" % CONFIG_LOC)

def get(key=None, default=None):
    global config
    if key == None: 
        return config
    
    c=config
    chain=key.split(".")
    for k in chain:
        if k in c: c=c[k]
        else: return default
        
    return c

def set(key, value, save=False):
    global config
    c=config
    chain=key.split(".")
    lastk=chain.pop()
    for k in chain:
        if k in c: c=c[k]
        else:
            c[k]={}
            c=c[k]
    c[lastk]=value
    if save:
        update(config)
        

def update(newjson):
    with open(CONFIG_LOC,'w') as cf:
        json.dump(newjson,cf)
    reload()

def save():
    global config
    update(config)

# Update config.json from sdcard if exits.
if CONFIG_SDCARD_UPDATE and utils.path_isfile(CONFIG_SDCARD_UPDATE):
    with utils.rw_sd:
        if utils.path_isfile(CONFIG_LOC):
            utils.copyfile(CONFIG_LOC, CONFIG_SDCARD_UPDATE+'.backup')
        utils.copyfile(CONFIG_SDCARD_UPDATE, CONFIG_LOC)
        os.remove(CONFIG_SDCARD_UPDATE)

reload()