#!/usr/bin/env python

"""this class handles the config stuff and presents an easy interface for the other classes
"""

from ConfigParser import *
import os
import sys
import time

if sys.platform in ('win32', 'cli'):
    defaultConfigFile = "unifi_lab.ini"
else:
    defaultConfigFile = "/etc/unifi_lab/unifi_lab.ini"

# Weekday as a decimal number [0(Sunday),6].
# we map it by hand as %A depends on the local language --> we use %w
mapSchedule = { 0: "onOffScheduleSunday", 
                1: "onOffScheduleMonday", 
                2: "onOffScheduleTuesday", 
                3: "onOffScheduleWednesday", 
                4: "onOffScheduleThursday", 
                5: "onOffScheduleFriday", 
                6: "onOffScheduleSaturday"
               }
# we map it by hand as otherwise the local language will make problemes
mapDayOfTheWeek = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}

class ConfigManager:
    _config = None
    _configFile = None
    def __init__(self, configFile = None):
        # this is needed as the caller can provide None as parameter
        if not configFile:
            configFile = defaultConfigFile

        if not os.path.isfile(configFile):
            sys.stdout = sys.stderr
            print "Error: Cannot find config file %r" % configFile
            sys.exit(2)

 
        self._config = SafeConfigParser()
        self._config.read(configFile)
        self._configFile = configFile

    def getConfigFile(self):
        return self._configFile
        
        
    # General
    def getPidFile(self):
        return self._config.get("General", "pidFile")

    def getLogFile(self):
        return self._config.get("General", "logFile")

    def getErrorLogFile(self):
        return self._config.get("General", "errorLogFile")
    
    def getInterval(self):
        return int(self._config.get("General", "interval"))
    
    # Controller
    def getControllerHost(self):
        return self._config.get("Controller", "controllerHost")
        
    def getControllerUsername(self):
        return self._config.get("Controller", "controllerUsername", raw=True)
        
    def getControllerPassword(self):
        return self._config.get("Controller", "controllerPassword", raw=True)      
        
        
    # Mail    
    def getFromAddress(self):
        return self._config.get("Mail", "fromAddress")
    
    def getToAddresses(self):
        tmp = []
        for address in self._config.get("Mail", "toAddresses").split(","):
            tmp.append(address.strip())
        return tmp

    def getSmtpServer(self):
        return self._config.get("Mail", "smtpServer")
          
          
    # Feature
    def getEnableMacAuth(self):
        return self._config.getboolean("Feature", "enableMacAuth")
        
    def getEnablePoorSignalReconnect(self):
        return self._config.getboolean("Feature", "enablePoorSignalReconnect")
        
    def getEnableSsidOnOffSchedule(self):
        return self._config.getboolean("Feature", "enableSsidOnOffSchedule")
        
    def getEnablePeriodicReboot(self):
        return self._config.getboolean("Feature", "enablePeriodicReboot")
   
   
    # MacAuth
    def getMacAuthListFile(self):
        return self._config.get("MacAuth", "macAuthListFile")    


    # PoorSignalReconnect
    def getPoorSignalBase(self):
        return self._config.get("PoorSignalReconnect", "poorSignalBase")
    
    def getPoorSignalThreshold(self):
        return self._config.getint("PoorSignalReconnect", "poorSignalThreshold")
        
    def getPoorSignalThresholdSeconds(self):
        return self._config.getint("PoorSignalReconnect", "poorSignalThresholdSeconds")
    
          
    # SsidOnOffSchedule
    def getOnOffScheduleApNamePrefix(self):
        return self._config.get("SsidOnOffSchedule", "onOffScheduleApNamePrefix")

    def getOnOffScheduleWlanList(self):
        return self._config.get("SsidOnOffSchedule", "onOffScheduleWlanList").split(',')
        
    def getOnOffScheduleForToday(self):
        """ return the schedule for today """
        return self._config.get("SsidOnOffSchedule", mapSchedule[int(time.strftime("%w", time.localtime()))]).split("-")

    
    # PeriodicReboot
    def getPeriodicRebootApNamePrefix(self):
        return self._config.get("PeriodicReboot", "periodicRebootApNamePrefix")
        
    def getRebootToday(self):
        """ 
            return the current day if today is a reboot day and None if not.
        """
        today = int(time.strftime("%w", time.localtime()))
        for day in self._config.get("PeriodicReboot", "periodicRebootDays").lower().split(","):
            if mapDayOfTheWeek[day] == today:
                return today
        return None
    
    def getPeriodicRebootTime(self):
        return self._config.get("PeriodicReboot", "periodicRebootTime")    

def main():
    """ Main program: parse command line and start processing .. only for Testing """
    myConfigManager = ConfigManager("unifi_lab_development.ini")
    print myConfigManager.getToAddresses()
    print myConfigManager.getLogFile()
    print myConfigManager.getEnablePeriodicReboot()
    print myConfigManager.getOnOffScheduleForToday()
    print myConfigManager.getRebootToday()
    print myConfigManager.getInterval()
    
if __name__ == '__main__':
    main()
