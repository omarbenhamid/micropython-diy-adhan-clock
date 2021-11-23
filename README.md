core module: Here go the core modules that are not updated (used by the autoupdater)
src module the rest.

config : will look for config.json in SDCARD if exists : imports it as main config and removes it
        a copy of current config.json is saved to "config.json.backup" in sdcard.
        
#Deployment:

```
export AMPY_PORT=COM3
ampy mkdir core
ampy put core/*.py core/

ampy mkdir src
ampy put src/*.py src/


ampy mkdir web
ampy put web/* web

ampy put main.py /

```

# Developer docs :

do not use PWM !! (PWM on pin 19 Disabled audio playing)