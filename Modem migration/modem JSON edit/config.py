# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/7/22

# config.ini for the_flasher script
# __author__ = "mabu@newtec.eu"

# This section defines the mode that the script will run in .. along with the choice to flash both banks consecutively
# script mode has two values either local or hub .. you will need to set the configuration of each mode accordingly
[script]
mode = hub
terminalsList = terminals.csv

# Configuration in case the script will be running from hub (TCS)
# num_of_modems indicates the number of terminals to be processed by the script in one run
# maintenance_window is set to True in case the script is meant to run in a maintenance window
# end_hour (in 24h format) indicates at which hour should the script stop e.g. you set 9 or 09 for 9am
# end_min indicates the min
# emd_hour and end_min can't be left empty if maintenance_window is set to True
[hub]
maintenance_window = True
end_hour = 12
end_min = 00

# Configuration in case the script will be running locally
[local]
modemIP = 192.168
.1
.1

# logging config
[logging]
logFile = gui_protector.log

# other generic settings
[generic]
sleepingTime = 8
