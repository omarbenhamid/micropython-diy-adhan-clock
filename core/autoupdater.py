'''
Created on Nov 18, 2021

@author: omar
'''

import sys
from utils import *
import hashlib, binascii
import urequests

AUTOUPDATER_URL_PREFIX="https://fcupdate.hifzo.com/"
#AUTOUPDATER_URL_PREFIX="http://obenhamid.me/fcupdate/"
AUTOUPDATER_LOCAL_DIR="/sdcard/update/"

try:
    AUTOUPDATER_UPDKEY=open('update.key','r').read()
except:
    AUTOUPDATER_UPDKEY=b'DEVUPDATEK'

"""
    Each component has a name and deploy_dir and a source.

    The source location (directory or web url) contains the following :

    <module_name>/
        vtag => a version number (can be timestamp for example)
        package => a tar file containing the update package
        patch.<vtag> => eventually a tar patch to existing vtag if deploy_dir has vtag 33 and patch.33 exists: it can be used for update.
        package.sig/patch.<vtag>.sig
                => contains SHA256(<package_file_content>+UPD_KEY+VTAG) where VTAG is the version number in decimal

    in deploy_dir there is a file called 'vtag' which indicates the last deployed version.


    The update process is the following :
    At check time (with wifi connected):
    1) Check source vtag :
        => if smaller or equal to deployed vtag : abandon.
        => if smaller or equal to vtag, already in local_updatedir/<module_name> abandon
    2) Check if there is a patch.<vtag> where <vtag> is the current vtag.
    3) If source is remote : Download vtag, XXXXX and XXXXX.sig were XXXXX is 'package' or 'patch.vtag'
        => Reboot.

    At boot time :
    1) Check local updates directory.
    2) If vtag is smaller or equal to deployed vtag : abandon.
    3) Verify if there is a patch.<vtag> where <vtag> is current <vtag> or a pakcage file.
        => In nothing abandon update.
    4) Check the found file against its .sig :
        => if does not exist or wrong signature : Rename all the files en x.reject and abandon.
    5) cleanup the deploy directory.
        => If 'package' is retained' remove all files
        => If 'patch' is reteained : remove only vtag from deploy if exists
    6) Untar the package/patch in deploy directory
    7) Update vtag file in deploy if everythign wentt well.
    6) Save the signature as 'sig' in deploy directory.
        => Reboot again.



"""

def _sign_file(infile, vtag):
    H=hashlib.sha256()
    BLK_SZ=4096
    blk=infile.read(BLK_SZ)
    while blk:
        H.update(blk)
        blk=infile.read(BLK_SZ)
    H.update(AUTOUPDATER_UPDKEY)
    H.update('%d' % vtag)
    return binascii.hexlify(H.digest())

def _getvtag(dir):
        try:
            with open(path_join(dir,'vtag'),'r') as v:
                return int(v.read())
        except Exception as err:
            return 0

class UpdatableModule():
    def __init__(self, name, deploy_dir):
        self.dir=deploy_dir
        self.name=name
        self.url=path_join(AUTOUPDATER_URL_PREFIX,name)
        self.locupdate=path_join(AUTOUPDATER_LOCAL_DIR,name)

    def download_updates(self):
        #read currenlty deployed vtag
        dvtag=_getvtag(self.dir)
        
        qrysuffix="?dev=%s&vtag=%d"%(get_unique_device_id(),dvtag)
        
        #1) Check source vtag : if smaller or equal to deployed vtag : abandon.
        with urequests.get(path_join(self.url,'vtag')+qrysuffix) as resp:
            if resp.status_code != 200:
                print("Cannot fetch vtag: bad http status %d " % resp.status_code )
                return False
            srcvtag = int(resp.content)
        
        if dvtag >= srcvtag:
            print("Deployed version already up to date")
            return False

        uvtag=_getvtag(self.locupdate)
        if uvtag >= srcvtag:
            try:
                self.validate_package_file(dvtag, uvtag)
                print("Update already downloaded and ready for install")
                return True
            except Exception as e:
                print(e)
                print("Bad local update file, re-downloading")


        #2) Check if there is a patch.<vtag> where <vtag> is the current vtag.

        packfile='patch.%d'%dvtag
        packresp=urequests.get(path_join(self.url,packfile)+qrysuffix)
        if packresp.status_code != 200:
            packresp.close()
            packfile='package' #Download the full package.
            packresp=urequests.get(path_join(self.url,packfile)+qrysuffix)
        if packresp.status_code != 200:
            packresp.close()
            print("Cannot fetch package")
            return False

        # 3) If source is remote : delte local dir vtag, XXXXX and XXXXX.sig were XXXXX is 'package' or 'patch.vtag'
        #    and last write vtage to vtag file in local update dir.
        #    => Reboot.


        #Downloading new package files
        packurl=path_join(self.url,packfile)
        packpath=path_join(self.locupdate,packfile)
        print("Downloading update package for version : %d" % srcvtag)
        with rw_sd:
            #Cleanup local update directory
            rmdir_deep(self.locupdate)
            makedirs(self.locupdate)
            with open(packpath,'wb') as outf, packresp:
                copyfileobj(packresp.raw,outf)
                
            with open(packpath+'.sig','wb') as outf, \
                urequests.get(packurl+'.sig'+qrysuffix) as resp:
                if resp.status_code != 200:
                    print("Cannot find signature file for package, aborting")
                    return False
                copyfileobj(resp.raw,outf)
            

            with open(path_join(self.locupdate,'vtag'),'w') as outf:
                outf.write(str(srcvtag))
            
            print("Update package downloaded")
            return True

    def validate_package_file(self, currvtag, updatevtag):
        """
        Find and verify package file
            Return tuple : path,ispatch : is patch is boolean saying wether is is a patch update or full package.
            Raise exception in case of error (like bad signature)

        """
        dvtag=currvtag
        uvtag=updatevtag

        #3) Verify if there is a patch.<vtag> where <vtag> is current <vtag> or a pakcage file.
        packfile=path_join(self.locupdate,'patch.%d'%dvtag)
        patch=True
        if not path_isfile(packfile):
            packfile=path_join(self.locupdate,'package')
            patch=False

        if not path_isfile(packfile):
            # => In nothing abandon update, will not be retired as vtag file was removed
            raise Exception("No suitable package file for update, ignoring update")


        #4) Check the found file against its .sig :
        # => if does not exist or wrong signature abandon.
        try:
            with open(packfile+'.sig','rb') as sigf:
                sig=sigf.read().strip()
        except:
            raise Exception("Cannot read signature file for package, abandoning")

        with open(packfile) as pfile:
            if sig != _sign_file(pfile, uvtag):
                raise Exception("Wrong signature for package")
        return packfile, patch

    def deploy_updates(self):
        from upip import tarfile as utarfile
        #At boot time :
        #1) Check local updates directory.
        dvtag=_getvtag(self.dir)
        uvtag=_getvtag(self.locupdate)

        #2) If vtag is smaller or equal to deployed vtag : abandon.
        if uvtag <= dvtag:
            print("Deployed version is up to date")
            return False

        try:
            packfile, patch=self.validate_package_file(dvtag, uvtag)
        except Exception as e:
            print(e)
            return False

        with rw_sd:
            #Prevent this update to be tried twice
            os.rename(path_join(self.locupdate,'vtag'), path_join(self.locupdate,'vtag.started'))

            #5) cleanup the deploy directory.
            p=path_join(self.dir,'vtag')
            if path_exists(p):
                os.remove(p)

            if not patch:
                #  => If 'package' is retained' remove all files
                rmdir_deep(self.dir)
                makedirs(self.dir)

            #6) Untar the package/patch in deploy directory
            t = utarfile.TarFile(packfile)
            for i in t:
                fp=path_join(self.dir,i.name)
                print("Updating %s" % fp)
                if i.type == utarfile.DIRTYPE:
                    makedirs(fp)
                else:
                    f = t.extractfile(i)
                    with open(fp, "wb") as outf:
                        copyfileobj(f, outf)
            os.remove(packfile)
            #7) Update vtag file.
            with open(path_join(self.dir,'vtag'),'w') as vtf:
                vtf.write('%d' % uvtag)

            #6) Save the signature as 'sig' in deploy directory.
            os.rename(path_join(self.locupdate,'vtag.started'), path_join(self.locupdate,'vtag.done'))

        return True

MODULES=[
    UpdatableModule('salatimes/annur.de','/sdcard/times'),
    UpdatableModule('app/main','/update'),
    UpdatableModule('app/web','/web'),
    UpdatableModule('app/audiodata','/sdcard/audiodata')
]

def download_updates():
    ret=False
    for mod in MODULES:
        print("check "+mod.name)
        ret=mod.download_updates() or ret
    return ret

def deploy_updates():
    ret=False
    for mod in MODULES:
        print("deploy "+mod.name)
        ret=mod.deploy_updates() or ret
    return ret

