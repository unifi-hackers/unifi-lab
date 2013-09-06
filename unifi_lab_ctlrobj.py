#############################################################################
## UniFi-Lab v0.0.2                                                        ##
#############################################################################
##Copyright (c) 2012, Ubiquiti Networks
##All rights reserved.
##
##Redistribution and use in source and binary forms, with or without
##modification, are permitted provided that the following conditions are met:
##    * Redistributions of source code must retain the above copyright
##      notice, this list of conditions and the following disclaimer.
##    * Redistributions in binary form must reproduce the above copyright
##      notice, this list of conditions and the following disclaimer in the
##      documentation and/or other materials provided with the distribution.
##    * Neither the name of the Ubiquiti Networks nor the
##      names of its contributors may be used to endorse or promote products
##      derived from this software without specific prior written permission.
##
##THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
##ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
##WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
##DISCLAIMED. IN NO EVENT SHALL UBIQUITI NETWORKS BE LIABLE FOR ANY
##DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
##(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
##LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
##ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
##(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
##SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#############################################################################
import os
import json
import time
from urllib import urlencode
import urllib2

class MyCtlr:
    ###############################################################
    ## CONTROLLER PARAMETERS                                     ##
    ###############################################################
    curl = ""
    ctlr_ip = ""
    ctlr_username = ""
    ctlr_password = ""
    ctlr_url = ""
    debug = 0

    ###############################################################
    ## Initialization                                            ##
    ###############################################################
    def __init__(self, ip, ctlr_web_id, ctlr_web_pw):
        self.ctlr_ip = ip
        self.ctlr_username = ctlr_web_id
        self.ctlr_password = ctlr_web_pw
        self.ctlr_url = "https://"+ip+":8443/"
        self._cookie=None

    ###############################################################
    ## CONTROLLER FUNCTIONS                                      ##
    ###############################################################
    def curl(self,func,data=None):
        """ Need to make error checking"""
        req = urllib2.Request(self.ctlr_url+func,data)
        if self._cookie:
            req.add_header("set-cookie", self._cookie)
        uo=urllib2.urlopen(req)
        self._cookie = uo.headers.dict.get('set-cookie', self._cookie)
        d = uo.read()
        return d

    def make_datastr(self, ll):
        dstr = ""
        for couple in ll:
            dstr = dstr + str(couple[0]) + "=" + str(couple[1]) + "&"
        return dstr[:-1]

    def make_jsonstr(self, ll):
        jstr = ""
        for couple in ll:
            jstr = jstr + "\"" + str(couple[0]) + "\":" + couple[1] + ","
        return "{" + jstr[:-1] + "}"

    def decode_json(self, jstr):
        decoded = json.loads(jstr)
        return json.loads(json.dumps(decoded["data"]))

    def ctlr_login(self):
        return self.curl ("login", self.make_datastr([["login","login"],["username",self.ctlr_username],["password",self.ctlr_password]]))

    def ctrl_stat_user_blocked(self):
        return self.curl("api/list/user", "json={\"blocked\":true}")

    def ctrl_list_group_members(self,group_id):
        return self.curl("api/list/user", "json="+json.dumps({'usergroup_id':group_id}))

    def ctrl_list_group(self):
        grouplist={}
        for g in self.decode_json(self.curl("api/list/usergroup")):
            grouplist[g['name']]=g
        return grouplist

    def ctlr_stat_device(self):
        return self.curl( "api/stat/device", self.make_datastr([["json",self.make_jsonstr([["_depth","2"],["test","null"]])]]) )

    def ctlr_stat_sta(self):
        return self.curl("api/stat/sta")

    def ctlr_wlan_conf(self):
        return self.curl("api/list/wlanconf")

    def ctlr_reboot_ap(self, apnamefilter=""):
        aplist = self.ctlr_stat_device()
        try:
            for ap in self.decode_json(aplist):
                if ap['state'] != 1:
                    continue
                if (ap.has_key('name') and ap['name'].startswith(apnamefilter)) or not ap.has_key('name'):
                    if ap.has_key('name'): print "Rebooting AP:", ap['name']
                    if not ap.has_key('name'): print "Rebooting AP:", ap['mac']
                    self.ctlr_mac_cmd(ap['mac'],"restart")
        except ValueError:
            pass        

    def ctlr_enabled_wlans_on_all_ap(self, apnamefilter="", target_wlan=[], en=True, wlans_forced_off=[]):
        aplist = self.ctlr_stat_device()
        wlanlist = self.ctlr_wlan_conf()
        if self.debug>0: print "Configure all Wireless LANs status to", en
        try:
            for ap in self.decode_json(aplist):
                if ap['state'] != 1:
                    continue
                if ap.has_key('name') and ap['name'].startswith(apnamefilter):
                    self.ctlr_enabled_wlans(ap['name'], target_wlan, en, aplist, wlanlist, wlans_forced_off)
                elif not ap.has_key('name'):
                    self.ctlr_enabled_wlans(ap['mac'], target_wlan, en, aplist, wlanlist, wlans_forced_off)
        except ValueError:
            pass

    # this function maintains enable/disable state of wlan, but will restore any security that was being overrided
    def ctlr_enabled_wlans(self, apname, target_wlan=[], en=True, aplist="", wlanlist="", wlans_forced_off=[]):
        if aplist == "": aplist = self.ctlr_stat_device()
        if wlanlist == "": wlanlist = self.ctlr_wlan_conf()
        owlan = []
        try:
            for ap in self.decode_json(aplist):
                twlan = list(target_wlan)
                if ap['state'] != 1:
                    continue
                if (ap.has_key('name') and apname == ap['name']) or (not ap.has_key('name') and apname == ap['mac']):
                    if len(twlan) > 0:
                        if ap['model'] == "U2O" or ap['model'] == "BZ2" or ap['model'] == "U7P":
                            for wlan in self.decode_json(wlanlist):
                                wlan['radio']='ng'
                                wlan['wlan_id']=wlan['_id']
                                del wlan['_id']
                                if wlan['name'] in twlan:
                                    wlan['enabled']=en                            
                                    owlan.append(wlan)
                                if wlan['name'] in wlans_forced_off:
                                    wlan['enabled']=False
                                    owlan.append(wlan)
                        if ap['model'] == "U5O" or ap['model'] == "U7P":
                            for wlan in self.decode_json(wlanlist):
                                wlan['radio']='na'
                                wlan['wlan_id']=wlan['_id']
                                del wlan['_id']
                                if wlan['name'] in twlan:
                                    wlan['enabled']=en
                                    owlan.append(wlan)
                                if wlan['name'] == "Neenah" or wlan['name'] == "Neenah-priv":
                                    wlan['enabled']=False
                                    owlan.append(wlan)
                    if self.debug>0 and ap.has_key('name'): print ap['name'], "all WLANs change to", en
                    if self.debug>0 and not ap.has_key('name'): print ap['mac'], "all WLANs change to", en
                    curlcmddata = self.make_datastr([["json",json.dumps(dict(wlan_overrides=owlan)).replace("\"",'%22')]])
                    curlcmdfunc = "api/upd/device/" + ap['_id']
                    if self.debug>0: print curlcmdfunc+" "+curlcmddata
                    if self.debug>0:
                        print self.curl(curlcmdfunc,curlcmddata)#os.popen(curlcmd).read()
                    else:
                        self.curl(curlcmdfunc,curlcmddata)#os.popen(curlcmd).read()
                    return True
        except ValueError:
            pass
        return False

    def ctlr_mac_cmd(self, target_mac, command):
        curlfunc="api/cmd/stamgr"
        if command == "block":
            curlcmd = self.make_datastr([["json",json.dumps(dict(mac=target_mac,cmd="block-sta")).replace("\"",'%22')]])
        elif command == "unblock":
            curlcmd = self.make_datastr([["json",json.dumps(dict(mac=target_mac,cmd="unblock-sta")).replace("\"",'%22')]])
        elif command == "reconnect":
            curlcmd = self.make_datastr([["json",json.dumps(dict(mac=target_mac,cmd="kick-sta")).replace("\"",'%22')]])
        elif command == "restart":
            curlfunc="api/cmd/devmgr"
            curlcmd = self.make_datastr([["json",json.dumps(dict(mac=target_mac,cmd="restart")).replace("\"",'%22')]])
        if self.debug>0: print curlcmd
        if self.debug>0:
            print self.curl(curlfunc, curlcmd)
        else:
            self.curl(curlfunc, curlcmd)
        return True

    def ctlr_get_ap_stat_field(self, apname, tag, aplist=""):
        if aplist=="":
            aplist = self.ctlr_stat_device()
        try:
            for ap in self.decode_json(aplist):
                if ap.has_key('name') and apname == ap['name']:
                    return ap[tag]
        except ValueError:
            pass

    # pass a list of tags
    def ctlr_get_sta_stat_fields_by_mac(self, stamac, tag, stalist=""):
        if stalist=="":
            stalist = self.ctlr_stat_sta()
        try:
            for sta in self.decode_json(stalist):
                if sta.has_key('mac') and stamac == sta['mac']:
                    rtag = []
                    for t in tag:
                        rtag.append(sta[t])
                    return rtag
        except ValueError:
            pass

    def ctlr_get_all_sta_mac(self, stalist=""):
        sta_mac_list = []
        if stalist=="":
            stalist = self.ctlr_stat_sta()
        try:
            for sta in self.decode_json(stalist):
                if sta.has_key('mac'):
                    sta_mac_list.append(sta['mac'])
        except ValueError:
            pass
        return sta_mac_list

    def ctlr_get_sta_stat_fields_by_name(self, name, tag, stalist=""):
        if stalist=="":
            stalist = self.ctlr_stat_sta()
        #print str(stalist)
        try:
            for sta in self.decode_json(stalist):
                if sta.has_key('hostname') and name == sta['hostname']:
                    rtag = []
                    for t in tag:
                        rtag.append(sta[t])
                    return rtag
        except ValueError:
            pass
print "installing handler for correct redirect"
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor()))
