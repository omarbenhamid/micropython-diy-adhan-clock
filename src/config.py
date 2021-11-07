import json
import sys

config={}
def reload():
    global config
    try:
        with open('config.json','r') as f:
            config = json.load(f)
    except Exception as err:
        config = {}
        sys.print_exception(err)
        print("Failed to load config.json, ignored")

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
        self.update(config)
        

def update(newjson):
    with open('config.json','w') as cf:
        json.dump(newjson,cf)
    reload()

def save():
    global config
    update(config)
    
reload()