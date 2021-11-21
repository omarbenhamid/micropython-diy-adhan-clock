"""
Look at deploy in README.md
"""
import sys

sys.path.append('/core')
import utils
# Eventually check and perofom autoupdates.
sys.path.append('/update/src')
sys.path.append('/src')

utils.mount_sdcard(True)

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
    
def run():
    import fc_main