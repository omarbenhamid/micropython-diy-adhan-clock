"""
Look at deploy in README.md
"""
import sys

sys.path.append('/core')
import utils

utils.mount_sdcard(True)

import autoupdater

if autoupdater.deploy_updates():
    import machine
    machine.deepsleep(1)

_fsafe=utils.path_exists('/sdcard/failsafe.txt')
if _fsafe:
    print("Failsafe mode, use main.failsafe(False) or remove failsafe.txt in SDCard to run normal mode")

if not _fsafe and utils.path_exists('/update/vtag'):
    print("Runnning updated app, use main.failsafe(True) or create failsafe.txt in SDCard to force original app")
    sys.path.append('/update/src')
else:
    print("Running original app")
    sys.path.append('/src')

if not utils.path_exists('.block'):
    print("Staring main app, to block use the main.block(True) function")
    #TODO: check and perform autoupdates
    from fc_main import *
else:
    print("Blocked mode, to unblock use main.block(False), for manual start call main.run()")

def block(enable):
    import os
    if enable:
        open('.block','wb').write("haha")
    else:
        if utils.path_exists('.block'): 
            os.remove('.block')
        import machine
        machine.deepsleep(1)
        
def failsafe(enable):
    import os
    with utils.rw_sd:
        if enable:
            open('/sdcard/failsafe.txt','wb').write("haha")
        else:
            if utils.path_exists('/sdcard/failsafe.txt'): 
                os.remove('/sdcard/failsafe.txt')
    import machine
    machine.deepsleep(1)
    
def run():
    import fc_main