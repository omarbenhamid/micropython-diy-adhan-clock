'''
Created on 22 sept. 2019

@author: omar
'''

import network
from microDNSSrv import MicroDNSSrv
from microWebSrv import MicroWebSrv
import time

wlan = None
wlan = network.WLAN(network.AP_IF)
wlan.config(essid="MySmartClock")

dns = None
web = None

# The RTC
ds = None
# The salat database
sdb = None

@MicroWebSrv.route('/status')
def getStatus(cli, resp, message=""):
    with open("status.html",'r') as f:
        template = f.read()
    y,m,d,h,mi,_,_,_ = time.localtime()
    
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
        print('Set time ! to ', data["date"], data["time"])
    
    getStatus(cli,resp,"Time update not yet implemented")

def start(ds, sdb):
    global dns, web
    ds = ds
    sdb = sdb
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
    if web != None:
        web.Stop()
        web = None
    if dns != None:
        dns.Stop()
        dns = None
    wlan.active(0)
