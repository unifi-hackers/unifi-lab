#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

"""
    Refer to http://wiki.ubnt.com/UniFi_Lab
    Ubiquiti Networks UniFi-Lab consists of following tools:
        1. MAC list authentication
        2. Poor Signal Quality reconnection (based on Signal Strength or RSSI value)
        3. SSID schedule on/off
        4. Periodic reboot APs (introduced in v0.0.2)
        
    usage: unifi_lab [start|stop|restart] <options>

    -c  use other config file than /etc/unifi_lab/unifi_lab.ini
    -f  do not fork into background ... only good for debugging
    -h  this help
    
    the start|stop|restart paramter is not available on Windows .. so don't use it there
    
"""

# Global FIXMES ....
# FIXME: code does not check if curl is installed, should be done



# FIXME: move that to the config file or extra file
errorMessageText = """Subject: UniFi Labs Error

Hi!

Following error occurred

%(error)s

Yours,
UniFi Labs
"""



###################### no changes beyond that line needed ####################

# shipped with python
import sys
import time
import logging
import logging.handlers
import traceback
import getopt
import smtplib
from email.MIMEText import MIMEText
import re

# shipped with unifi_lab
import config_manager
import daemon
import unifi_lab_ctlrobj

################ helper functions ################

# logging is global, as we need it aways
# we're logging minimal
logLevel = logging.INFO
log = logging.getLogger('Mylog')
log.setLevel(logLevel)

def logError(e):
    """ centralised logging method """
    msg = "=========\n"
    # args can be empty
    if e.args:
        if len(e.args) > 1:
            msg += str(e.args) + "\n"
        else:
            msg += e.args[0] + "\n"
    else:
        # print exception class name
        msg += str(e.__class__) + "\n"
    msg += "---------" + "\n"
    msg += traceback.format_exc() + "\n"
    msg += "=========" + "\n"
    log.error(msg)
    return msg

def sendMail(text, config):
    """ mails a mail with the specified text """
    # build mail                                                                                                                                                                                                                
    contentLines = text.splitlines()
    # Create a text/plain message                                                                                                                                                                                               
    msg = MIMEText('\n'.join(contentLines[2:]), _charset = "utf-8")
    msg['Subject'] = contentLines[0][len("Subject: "):]
    msg['From'] = config.getFromAddress()
    msg['To'] = ",".join(config.getToAddresses())
    msg['Date'] = time.strftime('%a, %d %b %Y %H:%M:%S +0000', time.gmtime())

    # Send the message via our own SMTP server, but don't include the                                                                                                                                                           
    # envelope header.
    try:
        s = smtplib.SMTP()
        s.connect(config.getSmtpServer())
        s.sendmail(config.getFromAddress(), config.getToAddresses() , msg.as_string())
        s.close()
    except:
        print "Critical: Unable to send mail!"


############### main class ######################

class UniFiLab:
    _config = None
    _ctlr = None
    _stationList = None
    _stationRssi = {}
    _haveRebootedThisDay = None

    def __init__(self, configManager):
        """ init method of the object, which sets all up for the other methods"""
        self._config = configManager
        self._ctlr = unifi_lab_ctlrobj.MyCtlr(configManager.getControllerHost(),
                                              configManager.getControllerUsername(),
                                              configManager.getControllerPassword())
        self.interval = configManager.getInterval()
        # do a first login to make sure we can conect to the controller, before going to the background
        # FIXME: does not raise a exception if login does not work
        self._ctlr.ctlr_login()
        self._stationList = self._ctlr.ctlr_stat_sta()

    def updateStationList(self):
        """
            only one place should update the station list, and maybe we want to use the do* methods without 
            the continuousLoop method
        """
        self._stationList = self._ctlr.ctlr_stat_sta()

    def doMacAuth(self):
        """
            if a station was already blocked in controller, current implementation does unblock it
            if it is in the mac auth list
        """

        groups = self._ctlr.ctrl_list_group()
        mac_auth_list = [] # [line.strip() for line in open(self._config.getMacAuthListFile(),'r')]
        pattern = r'\S?(?:(?P<mac>(?:[\da-f]{2}[:-]){5}[\da-f]{2})|(?:\"(?P<whitegroup>\w+?)\"))\S?(?:#.*)?'
        for line in open(self._config.getMacAuthListFile(),'r'):
            m = re.match(pattern, line, re.I)
            if not m:
                log.error('Wrong line in config %s'%line)
                continue
            m = m.groupdict()
            if m['mac']:
                mac_auth_list += m['mac'].lower().replace('-',':')
            if m['whitegroup']:
                str_whitelist = self._ctlr.ctrl_list_group_members(groups[m['whitegroup']]['_id'])
                mac_whitelist = self._ctlr.ctlr_get_all_sta_mac(stalist=str_whitelist)
                mac_auth_list = mac_auth_list + mac_whitelist                
            pass
#        print "whitelist:%s"%mac_auth_list

        cur_asso_list = self._ctlr.ctlr_get_all_sta_mac(self._stationList)
        for mac in cur_asso_list:
            if mac not in mac_auth_list:
                log.info("[MAC Auth] This MAC needs to be blocked: %s", mac)
                # block this station
                self._ctlr.ctlr_mac_cmd(mac,"block")
            else:
                pass##log.info("[MAC Auth] This MAC is okay: %s " % mac)
 
        str_blockedlist = self._ctlr.ctrl_stat_user_blocked()
        mac_blockedlist = self._ctlr.ctlr_get_all_sta_mac(stalist=str_blockedlist)
#        print "blacklist:%s"%mac_blockedlist
        for mac in mac_auth_list:
            if mac in mac_blockedlist:
                log.info("[MAC Auth] This MAC needs to be unblocked: %s", mac)
                # unblock this station
                self._ctlr.ctlr_mac_cmd(mac,"unblock")                
        return


    def doPoorSignalReconnect(self):
        """
            if a station falls between rssi threshold_low and threshold_high for X seconds, then reconnect the station
            the idea is that, the de-auth normally triggers the station to search for another AP with better signals
            and then roams to that ap.
            NOTE UniFi controller GUI does not display RSSI value directly; it only shows Signal strength
            NOTE RSSI = Signal value - Noise Value (depends on the environment, usually -90 dBm)
            By setting in the unifi_lab.init.config file, you can choose either do it based on Signal Strength or RSSI    
        """
        
        sig_reconn_threshold = self._config.getPoorSignalThreshold()
        sig_reconn_threshold_seconds = self._config.getPoorSignalThresholdSeconds()
        poor_signal_base = self._config.getPoorSignalBase().lower()
        
        cur_asso_list = self._ctlr.ctlr_get_all_sta_mac(self._stationList)
        for mac in cur_asso_list:
            # initialization
            if not mac in self._stationRssi:
                self._stationRssi[mac] = time.time()
                
            if poor_signal_base == "signal":
                sta_stat = self._ctlr.ctlr_get_sta_stat_fields_by_mac(mac, ["signal"], self._stationList)
            else:
                sta_stat = self._ctlr.ctlr_get_sta_stat_fields_by_mac(mac, ["rssi"], self._stationList)
                
            ss = sta_stat[0]
            if self._stationRssi[mac] == 0:              # the station just reconnected back
                self._stationRssi[mac] = time.time()
                
            if ss <= sig_reconn_threshold:
                log.info("[Poor Sig] Station %s %s %s is less than threshold, first occurred at %s" % (mac, poor_signal_base, ss, self._stationRssi[mac]))
                if time.time() - self._stationRssi[mac] > sig_reconn_threshold_seconds:
                    log.info("[Poor Sig] Reconnect the station %s" % mac)
                    # reconnect the client
                    self._ctlr.ctlr_mac_cmd(mac,"reconnect")
                    self._stationRssi[mac] = 0
            else:
                log.info("[Poor Sig] Station %s %s %s is okay"  % (mac, poor_signal_base, ss))
                self._stationRssi[mac] = time.time()
        return

    # Monday_ON and Monday_OFF time, all the way to Sunday
    def doSsidOnOffSchedule(self):
        def openHour(on, off):
            """
                this function decides if the Wifi is on or off
            """
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
        
        """
            this checks the day of the week and calls than openHour to check if need need to be
            on or off
        """
        power_on_time, power_off_time = self._config.getOnOffScheduleForToday()
        if openHour(power_on_time, power_off_time):
            log.info("[SSID Sche] Now is OPEN")
            self._ctlr.ctlr_enabled_wlans_on_all_ap(self._config.getOnOffScheduleApNamePrefix(),self._config.getOnOffScheduleWlanList(),True)
        else:
            log.info("[SSID Sche] NOW is CLOSED")
            self._ctlr.ctlr_enabled_wlans_on_all_ap(self._config.getOnOffScheduleApNamePrefix(),self._config.getOnOffScheduleWlanList(),False)

    def doPeriodicReboot(self):
        """
            this function is responsible for rebooting the UAPs at the specified time
        """
        today = self._config.getRebootToday()
        if today:
            # today would be a day to reboot, but have we already rebooted?
            if today != self._haveRebootedThisDay:
                # we've not rebooted today and today is a reboot-day
                # use self._haveRebootedThisDay to ensure that rebooting happens only once a day
                now = time.strftime("%H:%M", time.localtime())
                reboot_time = self._config.getPeriodicRebootTime()
                [reboot_hour,reboot_min] = reboot_time.split(':')
                [cur_hour,cur_min] = now.split(':')
                if (cur_hour == reboot_hour and cur_min >= reboot_min) or (cur_hour > reboot_hour):
                    reboot_ap_name_prefix = self._config.getPeriodicRebootApNamePrefix()
                    log.info("[REBOOT] Today is a reboot day")
                    log.info("[REBOOT] Selected time to reboot: %s" % reboot_time)
                    log.info("[REBOOT] Rebooting all APs with name prefix (and those without name): %s" % reboot_ap_name_prefix)
                    self._ctlr.ctlr_reboot_ap(reboot_ap_name_prefix)
                    self._haveRebootedThisDay = today
        else:
            self._haveRebootedThisDay = None


    def continuousLoop(self):
        """
            method which never terminates (until the process is killed). It runs every x second through the
            checks
        """
        

        # FIXME: the i3 und i4 stuff is not clean, need to clean it up later
        i3 = 0
        i4 = 0

        while True:
            
            startTime = time.time()
            # it is important that we keep running even if an error occurred, lets make sure
            try:
                self._ctlr.ctlr_login()
                # update station list
                self.updateStationList()
                
                if self._config.getEnableMacAuth():
                    self.doMacAuth()
                    
                if self._config.getEnablePoorSignalReconnect():
                    self.doPoorSignalReconnect()

                if self._config.getEnableSsidOnOffSchedule() and i3 > 11:       # do this once a minute is good enough, thus i3 > 11
                    self.doSsidOnOffSchedule()
                    i3 = 0
                i3 = i3 + 1

                if self._config.getEnablePeriodicReboot() and i4 > 11:
                    self.doPeriodicReboot()
                    i4 = 0
                i4 = i4 + 1
                
                
                # make sure that we runn every x seconds (including the time it took to work
                sleepTime = self.interval + 1 - (time.time() - startTime)

                if sleepTime < 0:
                    log.error("System is too slow for %d sec interval by %d seconds" % (self.interval, abs(int(sleepTime))))
                else:
                    time.sleep(sleepTime)
                    
            except Exception, e:
                # log error, and mail it ... and lets wait 10 times as long .... 
                sendMail(errorMessageText % {"error": logError(e)}, self._config)
                sleepTime = self.interval * 10 + 1 - (time.time() - startTime)
                if sleepTime < 0:
                    log.error("System is too slow for %d sec interval by %d seconds" % (10*interval, abs(int(sleepTime))))
                else:
                    time.sleep(sleepTime)


# Print usage message and exit
def usage(*args):
    sys.stdout = sys.stderr
    print __doc__
    print 50*"-"
    for msg in args: print msg
    sys.exit(2)


def main():
    """
        mail function which handles the stuff we only need if we're called directly but not 
        if we're used as module by an other module.
    """

    # on Windows we don't have start|stop|restart
    if sys.platform in ("linux2", "darwin"):
        parsingStartingPoint = 2
        if len(sys.argv) < 2:
            usage("Error: No paramter does not work on Unix-like systems.")
        # a small hack ... sorry
        if sys.argv[1] == "-h":
            print __doc__
            sys.exit()
        if not sys.argv[1] in ("start", "stop", "restart"):
            usage("Error: start|stop|restart is a minimum on Unix-like systems.")
    else:
        parsingStartingPoint = 1
        
    # options can be empty
    try:
        opts, args = getopt.getopt(sys.argv[parsingStartingPoint:], 'c:hf')
    except getopt.error, msg:
        usage(msg)
            
    configFile = None
    doNotFork = False
    for o, a in opts:
        if o == '-h':
            print __doc__
            sys.exit()
        if o == '-c':
            configFile = a
        if o == '-f':
            doNotFork = True

    myConfigManager = config_manager.ConfigManager(configFile)
    # we instance it here so its before we go into the background
    myUniFiLab = UniFiLab(myConfigManager)
    
    # on non Windows Systems we go into the background
    if not doNotFork and sys.platform in ("linux2", "darwin"):
        daemon.startstop(myConfigManager.getErrorLogFile(), pidfile=myConfigManager.getPidFile())

    # configure the logging
    _handler = logging.handlers.RotatingFileHandler(myConfigManager.getLogFile(), maxBytes=10*1024**2, backupCount=5)
    _handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    log.addHandler(_handler)

    log.info('Started')
    myUniFiLab.continuousLoop()
    log.info('Stopped')
    
if __name__ == '__main__':
    main()
