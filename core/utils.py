"""
    to write to sdcard use rw_sd context is to use this way :
    with utils.rw_sd:
        //Do stuff requiring write.
    SD Card is passed ot readonly mode directly after.
"""

import os
from micropython import const
import machine

S_IF_DIR=const(0x4000)
S_IF_FIL=const(0x8000)

def recurse(root, dirs=False):
    """ Recurse given directory,
    if dirs=True return also entries of directory
    => NB. direcotries are listed after their content.
    """
    for file in os.listdir(root):
        pth=root+'/'+file
        typ,_,_,_,_,_,_,_,mtime,_=os.stat(pth)
        if typ == S_IF_FIL:
            yield pth
        elif type == S_IF_DIR:
            for outcome in iterdir(pth): yield outcome
            if dirs: yield pth
            
def path_exists(path):
    """ Check if path exists """
    try:
        os.stat(path)
        return True
    except:
        return False
    
def path_isfile(path):
    """ Check if path is a regular file"""
    try:
        s=os.stat(path)
        return s[0]==S_IF_FIL
    except:
        return False
    
def path_isdir(path):
    """ Check if path exists and is a directory"""
    try:
        s=os.stat(path)
        return s[0]==S_IF_DIR
    except:
        return False
    
def copyfileobj(fsrc, fdst, length=16*1024):
    """copy data from file-like object fsrc to file-like object fdst"""
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)

def copyfile(path,to_path):
    with open(path,'rb') as inf:
        with open(to_path, 'wb') as outf:
            copyfileobj(inf,outf)
    
def rmdir_deep(path):
    for f in recurse_dir(path,dirs=False):
        os.remove(f)
    for f in recurse_dir(path,dirs=True):
        os.rmdir(f)
    os.rmdir(path)

class __WritableSDContext():
    def __enter__(self):
        mount_sdcard(False, False)
    
    def __exit__(self,*exc_info):
        mount_sdcard(True)

rw_sd=__WritableSDContext()

sdcard=None      
def mount_sdcard(readonly=True, ignoreerrors=True):
    global sdcard
    if not sdcard:
        sdcard=machine.SDCard()
    try:
        os.umount('/sdcard')
    except:
        pass
    try:
        os.mount(sdcard, '/sdcard', readonly=readonly)
        return True
    except Exception as e:
        if not ignoreerrors:
            raise
        sys.print_exception(e)
        print("SDCard Not Mounted : Error")
        return False