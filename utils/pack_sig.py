"""
    Usage pack_sig.py <signature_key> <version_tag> <package_file_path>
"""


import hashlib, binascii

AUTOUPDATER_UPDKEY=b'DEVUPDATEK'

def _sign_file(infile, vtag):
    H=hashlib.sha256()
    BLK_SZ=4096
    blk=infile.read(BLK_SZ)
    while blk:
        H.update(blk)
        blk=infile.read(BLK_SZ)
    H.update(AUTOUPDATER_UPDKEY)
    H.update(b'%d' % vtag)
    return binascii.hexlify(H.digest())

import sys

if len(sys.argv) != 4:
    print("Usage: pack_sig.py <signature_key> <version_tag> <package_file_path>")
    exit(1)
    
AUTOUPDATER_UPDKEY=sys.argv[1].encode('UTF-8')
print(_sign_file(open(sys.argv[3],'rb'), int(sys.argv[2])).decode('utf-8'))