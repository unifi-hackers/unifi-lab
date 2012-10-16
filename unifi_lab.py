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
##DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
##DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
##(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
##LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
##ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
##(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
##SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#############################################################################
##
## Refer to http://wiki.ubnt.com/UniFi_Lab
## Ubiquiti Networks UniFi-Lab consists of following tools:
##    1. MAC list authentication
##    2. Poor Signal Quality reconnection (based on Signal Strength or RSSI value)
##    3. SSID schedule on/off
##    4. Periodic reboot APs (introduced in v0.0.2)

import time
import unifi_lab_ctlrobj

ctlr_addr = ""
ctlr_username = ""
ctlr_password = ""

feature_mac_athentication = False
feature_rssi_reconnection = False
feature_ssid_schedule = False
feature_periodic_reboot = False

station_rssi = dict()

ap_name_prefix = ""
wlan_list = []
Monday_on = ""
Monday_off = ""
Tuesday_on = ""
Tuesday_off = ""
Wednesday_on = ""
Wednesday_off = ""
Thursday_on = ""
Thursday_off = ""
Friday_on = ""
Friday_off = ""
Saturday_on = ""
Saturday_off = ""
Sunday_on = ""
Sunday_off = ""

reboot_ap_name_prefix = ""
reboot_days = ""
reboot_time = ""
have_rebooted = False

# if a station was already blocked in controller,
# current implementation does NOT unblock it even
# if it is in the mac auth list
def MACAuth(ctlr, sta_list):
    cur_asso_list = ctlr.ctlr_get_all_sta_mac(sta_list)
    mac_auth_list = [line.strip() for line in open('unifi_lab_mac_auth.list','r')]
    for mac in cur_asso_list:
        if mac in mac_auth_list:
            print "[MAC Auth] This MAC is okay: ", mac
            pass
        else:
            print "[MAC Auth] This MAC needs to be blocked: ", mac
            # block this station
            ctlr.ctlr_mac_cmd(mac,"block")
    return

# if a station falls between rssi threshold_low and threshold_high for X seconds, then reconnect the station
# the idea is that, the de-auth normally triggers the station to search for another AP with better signals
# and then roams to that ap.
# NOTE UniFi controller GUI does not display RSSI value directly; it only shows Signal strength
# NOTE RSSI = Signal value - Noise Value (depends on the environment, usually -90 dBm)
# By setting in the unifi_lab.init.config file, you can choose either do it based on Signal Strength or RSSI
def PoorSignalReconn(ctlr, sta_list):
    cur_asso_list = ctlr.ctlr_get_all_sta_mac(sta_list)
    for mac in cur_asso_list:
        if station_rssi.has_key(mac):       # initialization
            pass
        else:
            station_rssi[mac] = time.time()
        if poor_signal_base == "Signal":
            sta_stat = ctlr.ctlr_get_sta_stat_fields_by_mac(mac, ["signal"], sta_list)
        else:
            sta_stat = ctlr.ctlr_get_sta_stat_fields_by_mac(mac, ["rssi"], sta_list)
        ss = sta_stat[0]
        if station_rssi[mac] == 0:              # the station just reconnected back
            station_rssi[mac] = time.time()
        if ss <= sig_reconn_threshold:
            print "[Poor Sig] Station", mac, poor_signal_base, ss, "is less than threshold, current time", time.time(), ", first occurred at", station_rssi[mac]
            if time.time() - station_rssi[mac] > sig_reconn_threshold_seconds:
                print "[Poor Sig] Reconnect the station", mac
                # reconnect the client
                ctlr.ctlr_mac_cmd(mac,"reconnect")
                station_rssi[mac] = 0
        else:
            print "[Poor Sig] Station", mac, poor_signal_base, ss, "is okay"
            station_rssi[mac] = time.time()
    return

def OpenHour(on, off):
    # on/off time in 24-Hour format. For example, 08:15 and 19:30
    now = time.strftime("%H:%M", time.localtime())
    [on_hour,on_min] = on.split(':')
    [off_hour,off_min] = off.split(':')
    [cur_hour,cur_min] = now.split(':')
    if cur_hour > off_hour:
        return False
    elif cur_hour == off_hour and cur_min > off_min:
        return False
    if cur_hour < on_hour:
        return False
    elif cur_hour == on_hour and cur_min < on_min:
        return False
    return True

# Monday_ON and Monday_OFF time, all the way to Sunday
def SSIDSch(ctlr):
    today_is = time.strftime("%a", time.localtime())
    if today_is == "Mon":
        power_on_time = Monday_on;  power_off_time = Monday_off
    if today_is == "Tue":
        power_on_time = Tuesday_on;  power_off_time = Tuesday_off
    if today_is == "Wed":
        power_on_time = Wednesday_on;  power_off_time = Wednesday_off
    if today_is == "Thu":
        power_on_time = Thursday_on;  power_off_time = Thursday_off
    if today_is == "Fri":
        power_on_time = Friday_on;  power_off_time = Friday_off
    if today_is == "Sat":
        power_on_time = Saturday_on;  power_off_time = Saturday_off
    if today_is == "Sun":
        power_on_time = Sunday_on;  power_off_time = Sunday_off
    if OpenHour(power_on_time, power_off_time):
        print "[SSID Sche] TODAY is ", today_is, "NOW is OPEN"
        ctlr.ctlr_enabled_wlans_on_all_ap(ap_name_prefix,wlan_list,True)
    else:
        print "[SSID Sche] TODAY is ", today_is, "NOW is CLOSE"
        ctlr.ctlr_enabled_wlans_on_all_ap(ap_name_prefix,wlan_list,False)
    return

def PeriodicReboot(ctlr):
    global have_rebooted
    today_is = time.strftime("%a", time.localtime())
    if today_is in reboot_days:
        if have_rebooted == False:
            #use have_rebooted to ensure that rebooting happens only once a day
            now = time.strftime("%H:%M", time.localtime())
            [reboot_hour,reboot_min] = reboot_time.split(':')
            [cur_hour,cur_min] = now.split(':')
            if (cur_hour == reboot_hour and cur_min >= reboot_min) or (cur_hour > reboot_hour):
                print "[REBOOT] Today is:", today_is, "\tSelected day(s) for reboot:", reboot_days
                print "[REBOOT] Now is:", now, "\tSelected time to reboot:", reboot_time
                print "[REBOOT] Rebooting all APs with name prefix (and those without name):", reboot_ap_name_prefix
                ctlr.ctlr_reboot_ap(reboot_ap_name_prefix)
                have_rebooted = True
    else:
        have_rebooted = False

# read from config file to initialize
config_file = open('unifi_lab.init.config','r')
for line in config_file:
    if line[0] == '#':
        pass
    else:
        try:
            [var,val] = line.strip().split('=')
            print "> ", var, val
            if var == "CTLR_ADDR":  ctlr_ip = val
            elif var == "CTLR_USERNAME":                        ctlr_username = val
            elif var == "CTLR_PASSWORD":                        ctlr_password = val
            elif var == "FEATURE_MAC_AUTH" and val == "True":    feature_mac_athentication = True
            elif var == "FEATURE_POOR_SIGNAL_RECONN" and val == "True": feature_rssi_reconnection = True
            elif var == "POOR_SIGNAL_BASE":                     poor_signal_base = val
            elif var == "SIGNAL_THRESHOLD":                     sig_reconn_threshold = int(val)
            elif var == "SIGNAL_THRESHOLD_SECONDS":             sig_reconn_threshold_seconds = int(val)
            elif var == "FEATURE_SSID_SCH" and val == "True":   feature_ssid_schedule = True
            elif var == "WLAN_LIST":                            wlan_list = val.split(',')
            elif var == "AP_NAME_PREFIX" and val is not None:   ap_name_prefix = val
            elif var == "MONDAY_ON":                            Monday_on = val
            elif var == "MONDAY_OFF":                           Monday_off = val
            elif var == "TUESDAY_ON":                           Tuesday_on = val
            elif var == "TUESDAY_OFF":                          Tuesday_off = val
            elif var == "WEDNESDAY_ON":                         Wednesday_on = val
            elif var == "WEDNESDAY_OFF":                        Wednesday_off = val
            elif var == "THURSDAY_ON":                          Thursday_on = val
            elif var == "THURSDAY_OFF":                         Thursday_off = val
            elif var == "FRIDAY_ON":                            Friday_on = val
            elif var == "FRIDAY_OFF":                           Friday_off = val
            elif var == "SATURDAY_ON":                          Saturday_on = val
            elif var == "SATURDAY_OFF":                         Saturday_off = val
            elif var == "SUNDAY_ON":                            Sunday_on = val
            elif var == "SUNDAY_OFF":                           Sunday_off = val
            elif var == "FEATURE_PERIODIC_REBOOT" and val == "True":   feature_periodic_reboot = True
            elif var == "REBOOT_AP_NAME_PREFIX":                reboot_ap_name_prefix = val
            elif var == "REBOOT_DAYS":                          reboot_days = val.split(',')
            elif var == "REBOOT_TIME":                          reboot_time = val
        except ValueError:
            pass
config_file.close()


ctlr = unifi_lab_ctlrobj.MyCtlr(ctlr_ip,ctlr_username,ctlr_password)
i3 = 0
i4 = 0
while True:
    ctlr.ctlr_login()
    stations_list = ctlr.ctlr_stat_sta()
    
    if feature_mac_athentication:
        MACAuth(ctlr,stations_list)
        
    if feature_rssi_reconnection:
        PoorSignalReconn(ctlr,stations_list)

    if feature_ssid_schedule and i3 > 11:       # do this once a minute is good enough, thus i3 > 11
        SSIDSch(ctlr)
        i3 = 0
    i3 = i3 + 1

    if feature_periodic_reboot and i4 > 11:
        PeriodicReboot(ctlr)
        i4 = 0
    i4 = i4 + 1
    
    time.sleep(5)

