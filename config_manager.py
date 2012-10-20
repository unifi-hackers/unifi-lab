#!/usr/bin/env python

"""this class handles the config stuff and presents an easy interface for the other classes
"""

from ConfigParser import *
import os
import sys

defaultConfigFile = "/etc/unifi_lab/unifi_lab.ini"

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
          

def main():
    """ Main program: parse command line and start processing .. only for Testing """
    myConfigManager = ConfigManager("unifi_lab_development.ini")
    print myConfigManager.getToAddresses()
    print myConfigManager.getLogFile()
    print myConfigManager.getPidFile()

    
if __name__ == '__main__':
    main()
