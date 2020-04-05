import json

try:
    with open('config.json','r') as f:
        config = json.load(f)
except Exception as err:
    config = {}
    sys.print_exception(err)
    print("Failed to load config.json, ignored")

def get(key):
    return config.get(key)