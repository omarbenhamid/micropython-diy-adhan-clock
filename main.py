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
    
# Eventually check and perofom autoupdates.
sys.path.append('/update/src')
sys.path.append('/src')

if not utils.path_exists('.block'):
    print("Staring main app, to block use the main.block() function")
    #TODO: check and perform autoupdates
    from fc_main import *
else:
    print("Blocked mode, to unblock use main.unblock(), for manual start call main.run()")

def block():
    import os
    open('.block','wb').write("haha")
    
def unblock():
    import os
    if utils.path_exists('.block'): 
        os.remove('.block')
    import machine
    machine.deepsleep(1)
    
def run():
    import fc_main