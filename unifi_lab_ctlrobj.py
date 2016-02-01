#############################################################################
## UniFi-Lab v0.0.3                                                        ##
#############################################################################
##Copyright (c) 2016, Ubiquiti Networks
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
import ssl
import cookielib

from unifi.controller import Controller

class MyCtlr:
    ###############################################################
    ## CONTROLLER PARAMETERS                                     ##
    ###############################################################
    ctlr_ip = ""
    ctlr_username = ""
    ctlr_password = ""
    ctlr_url = ""
    debug = 1

    ###############################################################
    ## Initialization                                            ##
    ###############################################################
    def __init__(self, ip, ctlr_web_id, ctlr_web_pw, ctrl_web_port, ctrl_web_version):
        self.ctlr_ip = ip
        self.ctlr_username = ctlr_web_id
        self.ctlr_password = ctlr_web_pw
        #self.ctlr_url = "https://"+ip+":8443/"
        self.ctrl_web_port = ctrl_web_port
        self.ctrl_web_version = ctrl_web_version

    ###############################################################
    ## CONTROLLER FUNCTIONS                                      ##
    ###############################################################
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
        self.c = Controller(self.ctlr_ip,self.ctlr_username,self.ctlr_password,self.ctrl_web_port,self.ctrl_web_version)
        return self.c

    def ctrl_stat_user_blocked(self):
        users = self.c.get_users()
	blocked = []
        for user in users:
             if user.has_key('blocked'):
                  if str(user['blocked']) == 'True':
                       blocked.append(user)
        return blocked

    def ctrl_list_group_members(self,group_id):
        users = self.c.get_users()
	group_users = []
        for user in users:
             if user.has_key('usergroup_id'):
                  if str(user['usergroup_id']) == group_id:
                       group_users.append(user)
        return group_users

    def ctrl_list_essid_members(self,essid_id):
        users = self.c.get_clients()
	group_users = []
        for user in users:
             if user.has_key('essid'):
                  if str(user['essid']) == essid_id:
                       group_users.append(user)
        return group_users

    def ctrl_list_group(self):
        grouplist={}
        grouplist = self.c.get_user_groups()
        return grouplist

    def ctlr_stat_device(self):
        aps = self.c.get_aps()
        return aps

    def ctlr_stat_sta(self):
        clients = self.c.get_clients()
        return clients

    def ctlr_wlan_conf(self):
        wlan_conf = self.c.get_wlan_conf()
        return wlan_conf

    def ctlr_reboot_ap(self, apnamefilter=""):
        aplist = self.ctlr_stat_device()
        try:
            for ap in aplist:
                if not ap.has_key('state') or ap['state'] != 1:
                    continue
                if (ap.has_key('name') and ap['name'].startswith(apnamefilter)) or not ap.has_key('name'):
                    if ap.has_key('name'): print "Rebooting AP:", ap['name']
                    if not ap.has_key('name'): print "Rebooting AP:", ap['mac']
                    self.c.restart_ap(ap['mac'])
        except ValueError:
            pass        

    def ctlr_enabled_wlans_on_all_ap(self, apnamefilter="", target_wlan=[], en=True, wlans_forced_off=[]):
        aplist = self.ctlr_stat_device()
        wlanlist = self.ctlr_wlan_conf()
        if self.debug>0: print "Configure all Wireless LANs status to", en
        try:
            for ap in self.aplist:
                if not ap.has_key('state') or ap['state'] != 1:
                    continue
                if ap.has_key('name') and ap['name'].startswith(apnamefilter):
                    self.ctlr_enabled_wlans(ap['name'], target_wlan, en, aplist, wlanlist, wlans_forced_off)
                elif not ap.has_key('name'):
                    self.ctlr_enabled_wlans(ap['mac'], target_wlan, en, aplist, wlanlist, wlans_forced_off)
        except ValueError:
            pass

    def ctlr_mac_cmd(self, target_mac, command):
        if command == "block":
            self.c.block_client(target_mac)
        elif command == "unblock":
            self.c.unblock_client(target_mac)
        elif command == "reconnect":
            self.c.disconnect_client(target_mac)
        elif command == "restart":
            self.c.restart_ap(target_mac)
        return True

    def ctlr_get_ap_stat_field(self, apname, tag, aplist=""):
        if aplist=="":
            aplist = self.ctlr_stat_device()
        try:
            for ap in self.aplist:
                if ap.has_key('name') and apname == ap['name']:
                    return ap[tag]
        except ValueError:
            pass

    # pass a list of tags
    def ctlr_get_sta_stat_fields_by_mac(self, stamac, tag, stalist=""):
        if stalist=="":
            stalist = self.ctlr_stat_sta()
        try:
            for sta in stalist:
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
            for sta in stalist:
                if sta.has_key('mac'):
                    sta_mac_list.append(sta['mac'])
        except ValueError:
            pass
        return sta_mac_list

    def ctlr_get_sta_stat_fields_by_name(self, name, tag, stalist=""):
        if stalist=="":
            stalist = self.ctlr_stat_sta()
        try:
            for sta in self.stalist:
                if sta.has_key('hostname') and name == sta['hostname']:
                    rtag = []
                    for t in tag:
                        rtag.append(sta[t])
                    return rtag
        except ValueError:
            pass
