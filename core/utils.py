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
        elif typ == S_IF_DIR:
            for outcome in recurse(pth, dirs): yield outcome
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
    
def path_join(*args, sep='/'):
    """
        Join provided path segments using the sep kwarg as separator (/ by default)
        if the first provided segment starts with sep it is kept.
        
        ```
        >>> path_join('/toto//','titi','/tata')
        '/toto/titi/tata'
        >>> path_join('toto','titi','tata')
        'toto/titi/tata'
    """
    ret=sep.join(seg.strip(sep) for seg in args)
    if args[0].startswith(sep):
        return sep+ret
    else:
        return ret
    
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
    if not path_exists(path):
        return
    for f in recurse(path,dirs=False):
        os.remove(f)
    for f in recurse(path,dirs=True):
        os.rmdir(f)
    os.rmdir(path)

def makedirs(path, sep='/'):
    if path.startswith(sep):
        p=''
    else:
        p='.'
    for seg in path.strip(sep).split(sep):
        p=p+sep+seg
        if not path_exists(p): os.mkdir(p)
    
################# Writable SDCard ops
class __WritableSDContext():
    def __init__(self):
        self._depth=0
    def __enter__(self):
        if self._depth == 0:
            mount_sdcard(False, False)
        self._depth=self._depth+1
    
    def __exit__(self,*exc_info):
        self._depth=self._depth-1
        if self._depth == 0:
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
    
