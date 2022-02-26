core module: Here go the core modules that are not updated (used by the autoupdater)
src module the rest.

config : will look for config.json in SDCARD if exists : imports it as main config and removes it
        a copy of current config.json is saved to "config.json.backup" in sdcard.

#Trouble shoot
1. Create failsafe.txt file in the root of SDCARD to run the basic source.

1. The app/main update must have python files in src/ folder.

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

# Auto updates

# Update is formed of many components

Each component has a name and deploy_dir and a source. These are defined in core/autoupdater.py :

```
   UpdatableModule('salatimes/annur.de','/sdcard/times'),
   UpdatableModule('app/main','/updated'),
   UpdatableModule('app/web','/web'),
   UpdatableModule('app/core','/core'),
   UpdatableModule('app/audiodata','/sdcard/audiodata')
```

-
## Update source structure
The source location (directory or web url) contains the following :

<module_name>/
    vtag => a version number (can be timestamp for example)
    package => a tar file containing the update package
    patch.<vtag> => eventually a tar patch to existing vtag if deploy_dir has vtag 33 and patch.33 exists: it can be used for update.
    package.sig/patch.<vtag>.sig
            => contains SHA256(<package_file_content>+UPD_KEY+VTAG) where VTAG is the version number in decimal
             utils/pack_sig.py allows generating this signature.


in deploy_dir there is a file called 'vtag' which indicates the last deployed version.

# Update sources are :

1. /update directory of the sdcard
2. fcupdate.hifzo.com
