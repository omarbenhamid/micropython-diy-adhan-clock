'''
Created on 22 sept. 2019

@author: omar
'''

import network
from microDNSSrv import MicroDNSSrv
from microWebSrv import MicroWebSrv
import time
import sys
from util import localtime, settime

wlan = None
wlan = network.WLAN(network.AP_IF)
wlan.config(essid="MySmartClock")

dns = None
web = None


# The salat database
sdb = None

@MicroWebSrv.route('/status')
def getStatus(cli, resp, message=""):
    with open("status.html",'r') as f:
        template = f.read()
    y,m,d,h,mi,_,_,_ = localtime()
    
    resp.WriteResponseOk(contentType     = "text/html",
                                contentCharset  = "UTF-8",
        content = template.format(
            currentTime="%04d-%02d-%02d-T%02d:%02d" % (y,m,d,h,mi),
            message=message
        )
    )

@MicroWebSrv.route('/status','POST')
def updateConfig(cli, resp):
    data = cli.ReadRequestPostedFormData()
    if 'settime' in data:
        y,m,d = [int(x) for x in data["date"].split('-')]
        h,mi = [int(x) for x in data["time"].split(":")]
        settime(y,m,d,0,h,mi,0)
        
        return getStatus(cli,resp,"Time updated")
    
    if 'loadcsv' in data:
        try:
            sdb.importcsv(data['csv'])
            return getStatus(cli,resp,"Salat timetable updated successfully")
        except Exception as err:
            sys.print_exception(err)
            return getStatus(cli,resp,"Error with CSV data : %s" % str(err))
        
    return getStatus(cli,resp)

def start(_sdb):
    global dns, web, sdb
    sdb = _sdb
    ## Starting Wifi Access Poijnt
    wlan.active(1)
    ## Setting Up Capitve portal
    ip=wlan.ifconfig()[0]
    dns = MicroDNSSrv()
    web = MicroWebSrv()
    web.SetNotFoundPageUrl("http://my-smart-clock.wifi/status")  
    dns.SetDomainsList({"*":ip})
    dns.Start()
    web.Start(True)


def stop():
    global web,dns
    if web != None:
        web.Stop()
        web = None
    if dns != None:
        dns.Stop()
        dns = None
    wlan.active(0)

def is_started():
    return web != None
