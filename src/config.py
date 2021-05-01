import json

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
    
    return config.get(key, default)

def update(newjson):
    with open('config.json','w') as cf:
        json.dump(newjson,cf)
    reload()
    
reload()