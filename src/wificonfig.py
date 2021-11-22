'''
Created on 22 sept. 2019

@author: omar
'''

import network
from microDNSSrv import MicroDNSSrv
from microWebSrv import MicroWebSrv
import time
import sys
from rtc import localtime, settime
import json
import arch
import wifi
import config

wlan = network.WLAN(network.AP_IF)

dns = None
web = None


# The salat database
sdb = None
player = None

@MicroWebSrv.route('/status')
def getStatus(cli, resp, message=""):
    with open(arch.WEB_DIR+"/status.html",'r') as f:
        template = f.read()
    y,m,d,h,mi,_,_,_ = localtime()

    args = dict()
    args.update(('salat%dalm' % sidx, sdb.getsalarmdelay(sidx) or 0) for sidx in range(0,6))
    args.update(('salat%dvol' % sidx, sdb.getsvolume(sidx) or 0) for sidx in range(0,6))
    
    if not config.get('wifi'):
        message += """<br/>Wifi not configured : 
                <a href="/wifi"> click here to configure wifi </a>
                """
    if config.get('mawaqit'):
        mawaqitStatus = "Mawaqit.net connection configured"
    else:
        mawaqitStatus = "Mawaqit.net connection not configured"

    ctz=config.get('rtc',{}).get('timezoneDeltaMinutes',0)
    

    resp.WriteResponseOk(contentType     = "text/html",
                                contentCharset  = "UTF-8",
        content = template.format(
            currentTime="%04d-%02d-%02d-T%02d:%02d" % (y,m,d,h,mi),
            currentTzDelta=str(ctz),
            mawaqitStatus = mawaqitStatus,
            message=message,
            perfmode='awake' if config.get('alwaysAwake', True) else 'eco',
            **args
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
    if 'settz' in data:
        tzmin = int(data['tzmin'])
        c=config.get()
        if not 'rtc' in c:
            c['rtc']={}
        c['rtc']['timezoneDeltaMinutes']=tzmin
        config.update(c)
        
        return getStatus(cli,resp,"Timezone updated")
    if 'loadcsv' in data:
        try:
            sdb.import_csv(data['csvmonth'],data['csv'])
            return getStatus(cli,resp,"Salat timetable updated successfully")
        except Exception as err:
            sys.print_exception(err)
            return getStatus(cli,resp,"Error with CSV data : %s" % str(err))

    if 'updatenotif' in data:
        for sidx in range(0,6):
            sdb.setsalarmdelay(sidx, int(data['salat%dalm'%sidx]))
            sdb.setsvolume(sidx, int(data['salat%dvol'%sidx]))
        sdb.save()
    
    if 'updperfmode' in data:
        c=config.get()
        if data['perfmode']=='eco':
            c['alwaysAwake']=False
        else:
            c['alwaysAwake']=True
        config.update(c)
        
    player.say_reconfigured(sync=False)
    return getStatus(cli,resp)

@MicroWebSrv.route('/wifi')
def getWifiSetup(cli, resp, message=""):
    if not config.get("wifi") or not config.get("wifi").get("SSID"):
        message+="<br/>Wifi not configured"
        currSSID=""
    else:
        currSSID=config.get("wifi").get("SSID")
    
    ## List SSIDs
    wifi.conn.active(True)
    networks=''.join(
        '<option name="'+SSID.decode()+'">'+SSID.decode()+'</option>'
        for SSID,_,_,_,_,_ in wifi.conn.scan()
    )
    wifi.conn.active(False)
    
    with open(arch.WEB_DIR+"/wifi.html",'r') as f:
        template = f.read()
    resp.WriteResponseOk(contentType     = "text/html",
                                contentCharset  = "UTF-8",
        content = template.format(
            message=message,
            networks=networks,
            currSSID=currSSID
        )
    )

@MicroWebSrv.route('/wifi','POST')
def updateWifi(cli, resp):
    data = cli.ReadRequestPostedFormData()
    c=config.get()
    if 'deletewifi' in data:
        if 'wifi' in c:
            w=c['wifi']
            w['SSID']=''
            w['password']=''
            config.update(c)
        return getWifiSetup(cli, resp, "Wifi setup deleted")
    
    SSID=data['SSID']
    password=data['pass']
    if 'wifi' not in c:
        c['wifi']={'password':''}
    if password or SSID!=c['wifi'].get('SSID'): #Set password if SSID changes or password is set
        c['wifi']['password']=password
    c['wifi']['SSID']=SSID
    config.update(c)
    try:
        wifi.connect(timeoutmillis=30*1000)
        player.say_reconfigured(sync=False)
        return getWifiSetup(cli, resp, "Connected successully to "+SSID)
    except:
        player.say_reconfigured(sync=False)
        return getWifiSetup(cli, resp, "Failed to connect")

def start(_sdb, _player):
    global dns, web, sdb, player
    sdb = _sdb
    player=_player
    ## Starting Wifi Access Poijnt
    wlan.active(1)
    wlan.config(essid="MyFajrClock")
    ## Setting Up Capitve portal
    ip=wlan.ifconfig()[0]
    dns = MicroDNSSrv()
    web = MicroWebSrv()
    web.SetNotFoundPageUrl("http://my-fajr-clock.wifi/status")
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
