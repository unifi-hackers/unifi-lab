# Introduction
UniFi-Lab is collection of utilities that aims to help managing UniFi 
controller. UniFi-Lab interacts with UniFi controller through cURL, which is 
like a text-version browser, and is controlled by python scripts. You can think 
of UniFi-Lab as a robot IT that always monitors the controller and takes actions
when needed.

UniFi lab was initially made available through Ubiquiti Networks as example
how to instrument the UniFi API. As of writing thanks to this code drop others
have been inspired to create (even cleaner) interfaces to the UniFi API. For 
example have please have a look at Jakob Borg's unifi-api for Python 
(https://github.com/calmh/unifi-api).

# Features
## MAC Addresses White List
The UniFi controller will block any MAC that is not on the list.

## Poor Signals Reconnect
The UniFi controller will kick (aka reconnect) any stations that fall below 
assigned RSSI (or Signal Strength, depends on the configuration) threshold for 
assigned period. The idea is that, by forcing a station to reconnect, the 
station often goes to an AP with better signals to its eyes, therefore gets 
better performances.

This feature can also be used as blocking those stations below certain RSSI if 
the duration threshold is set to 1 second. This won't completely shut off a 
station since the station still can connect for 1 second before gets kick, but 
it surely will be very annoying and close to unusable wireless. We cannot simply
block a station every time it falls below a threshold. If we do that, we then 
have no idea when the station is back into the range. At this moment, only a 
connected station can be told RSSI on controller, it is a chicken and egg problem.

## WLAN On/Off Schedule
The UniFi controller will turn on/off selected WLANs on selected APs based on 
the specified daily schedules.

## AP Periodic Reboot
The controller will reboot selected APs on the specified days and time.

# Prerequisites
The UniFi-Lab utility needs to interact with the UniFi controller, therefore 
'''UniFi controller must be up and running'''. It also needs these two software installed
* Python 2.x
* Curl

Below we demonstrate installation steps in different operating systems.

## Debian 6.0
* This is a fresh Debian installed on a VMware, the Debian image can be 
downloaded at http://www.trendsigma.net/vmware/debian6t.html
* open a terminal and type 'python -V' to check if it is installed and which version it is
* the Python version I got is 2.6.6
* We also need curl. Since it is not in the system, we need to install it:
** In Debian GNOME desktop, "System" > "Administration" > "Synaptic Package Manager"
** Search for "curl"
** Mark the "Install" of curl and click "Apply" to install curl and dependent 
   packages
* bring up a new terminal and see if 'curl www.google.com' returns the text version of google page

## Windows
* Python can be downloaded from http://www.python.org/download. The version I 
installed is Python 2.7.3 which is the current production code. I don't think 
there is a version dependency for UniFiLab, so other nearby versions should work 
also.
* I am using "Windows X86-64 MSI Installer" of Python since I am using a Win7 Pro 64-bit laptop.
* After installation, Python is not in the 'Path' variable so we need to add that.
** Right click "Computer" > "Properties" > "Advanced system settings" > "Advanced" tab > "Environmental Variables", append "\;C:\\Python27\\" to the end of 'Path' System variables.
* cURL can be downloaded from http://www.paehl.com/open_source/?CURL_7.27.0, this is 32-bit
* The one I installed is "Download WITH SUPPORT SSL"
* Extract the zip file and there is a curl executable. Put it under UniFiLab scripts folder.
* Open a command line window and see if you can do 'python -V' and 'curl www.google.com' commands.

## Mac
* To my understanding, both python and curl come with OSX. Please let us know if it is not working there.

# Download
UniFi-Lab can be downloaded from here.

There are four files included in the UniFi-Lab,
* '''unifi_lab_production.ini''' => This is the configuration file of UniFi-Lab
* '''unifi_lab.py''' => This is the main execution script
* '''unifi_lab_ctlrobj.py''' => This has functions that we used to interact with the controller
* '''unifi_lab_mac_auth.list''' => This is used by MAC authentication feature. It contains the white list of allowed MAC addresses.

# Installation for Manual run
Create a directory and put above files under it.
Copy '''unifi_lab_production.ini''' to /etc/unifi_lab/unifi_lab.ini and modify for your environment

For Windows, make sure that curl.exe is also under the same folder.

# Execution
Modify the config file first according to your needs and environment. Then, in 
CLI, go to the directory, run "'''python unifi_lab.py'''" to start. To stop, 
press "Ctlr-C".  If you change the config file while running, you also need to
restart the UniFi-Lab to reflect these changes.

# Installation of Debian init scripts
The following was tested on Debian 6
* Unzip files to /usr/lib/unifi_lab/
* Copy '''unifi_lab_production.ini''' to /etc/unifi_lab/unifi_lab.ini and modify for your environment
* ln -s /usr/lib/unifi_lab/unifi_lab.init /etc/init.d/unifi_lab
* update-rc.d unifi_lab defaults

Now you can use /etc/init.d/unifi_lab start|stop|restart

# Configuration
The '''/etc/unifi_lab/unifi_lab.ini''' file contains the related parameters of UniFi-Lab features. Lines that start with ; are comments.
## [General] Section
The [General] section does not need changes unless you want your log or pid files in another location or with a different name
## [Controller] section
You must fill in the [Controller] section to point to your UniFi server.  These set controller ip address, login id and password
* controllerHost = 192.168.1.100
* controllerUsername = hello
* controllerPassword = world

## [Mail] section
Use the [Mail] section to configure email alerts
## [Feature] section
This section enables or disables unifi_lab features.  Use "True" or "False" values (Note: values are case sensitive)
## MAC addresses white list feature
There are no other parameters for MAC_AUTH. The white list file "unifi_lab_mac_auth.list" has allowed MAC addresses.  One MAC address per line. The UniFi-Lab will ask the controller to block any MAC that is not on the list. The white list file can be changed on the fly (meaning the UniFi-Lab reloads file constantly)
## Poor signals reconnect feature
* poorSignalBase = [Signal|RSSI].  You can reconnect a client based on its Signal Strength or RSSI (RSSI = Signal Strength - Noise Floor).
* poorSignalThreshold = N.  This depends on what you have set for the base, "N" is the threshold value. For example, if the base is set to Signal and threshold is -65, that means the UniFi-Lab will concern those clients who has signal strength below -65 dBm.
* poorSignalThresholdSeconds = M.  The controller will reconnect this client if it falls below the threshold for ''M'' seconds. For example, "poorSignalThresholdSeconds = 10" means 10 seconds.

## WLANs on/off schedule feature
* onOffScheduleApNamePrefix = [empty|prefix].  Leave this empty for all APs, or give an alias prefix to only affect those APs.
* onOffScheduleWlanList = wlan1,wlan2,wlan3,wlan4.  This is a list of WLANs that will be controlled by the scheduler, separated by a comma ",".
* onOffScheduleWlanOverrideOffList = wlan5,wlan6.  This is a list of WLANs that will be overridden to off permanently for these APs, separated by comma ','
* onOffScheduleMonday = 09:00-19:00
* onOffScheduleTuesday = 09:00-19:00
* onOffScheduleWednesday = 09:00-19:00
* onOffScheduleTursday = 09:00-19:00
* onOffScheduleFriday = 09:00-19:00
* onOffScheduleSaturday = 09:00-19:00
* onOffScheduleSunday= 09:00-19:00
* Above is the on/off schedule in 24-hr format.  Note: For fully ON day (AP enabled entire day), set to 00:00-24:00.  For fully OFF day (AP disabled entire day), set to 24:00-24:00.

## For Periodic Reboot feature
* periodicRebootApNamePrefix = [empty|prefix].  Leave this empty for all APs, or give an alias prefix to only affect those APs.
* periodicRebootDays = Mon,Tue,Wed,Thu,Fri,Sat,Sun.  Select which days (Case Sensitive) you want APs to be rebooted, separated by a comma ','
* periodicRebootTime = 23:30.  Time to reboot the APs, in 24-hr time format.

# Notes
## MAC Addresses White List
* If a MAC address is already blocked in the controller, adding it to the white list file will '''NOT''' automatically grant its access. The admin needs to manually "unblock" the MAC from the controller.

## POOR_SIGNAL_RECONN
* If a client is right at the borderline, you might risk reconnecting that client all the time and not able to service it at all. Enabling this feature may harm serviceability.

## SSID On/Off Scheduler
* To run this,  the AP config should '''NOT''' have any WLANs that are overrode with custom configurations.
* When the scheduler turns on/off of the WLANs in the list, other WLANs (those not in the list) will drop for a short moment.

## AP Periodic Reboot
* All selected APs will be reboot at the same time. There will be '''NO''' service during this time (~1 minute).
* This is controller asking APs to restart at the given time. The APs does '''NOT''' restart by itself.
