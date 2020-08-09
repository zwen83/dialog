# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/4/3

from modemPointsReader import modemPointsReader
from influxWriter import influxWriter
from HRCpointsReader import HRCpointsReader
from CPMpointsReader import CPMpointsReader
import threading
import rest


# platformList = {'AMI': '192.168.48.126:36006',
#                 'BCnet': '192.168.48.125:35006',
#                 'Bambu': '192.168.48.131:41006',
#                 'infokom1': '192.168.48.128:38006',
#                 'infokom2': '192.168.48.129:39006',
#                 'patrakom': '10.255.0.99:24006',
#                 'PSN2': '192.168.48.132:42006',
#                 'skyreach': '192.168.48.134:44006',
#                 'Telered': '192.168.48.130:40006',
#                 'TNIC': '192.168.48.136:46006',
#                 'TNIK': '192.168.48.137:47006',
#                 'Stella': '10.255.0.100:25006',
#                 }
platformList = {'BCnet': '192.168.48.125:35006'}

m = modemPointsReader('BCnet', '192.168.48.125:35006', 'hno', 'D!@10g', 'modemKPIs', 'forwardTotal', 'returnTotal')

data = m.getPoints()

for row in data[0]:
    print(row)
    w = influxWriter('192.168.48.42', 'root', 'root', 'test123', row)
    w.writer()
wFWD = influxWriter('192.168.48.42', 'root', 'root', 'test123', data[1][0])
wFWD.writer()
wRTN = influxWriter('192.168.48.42', 'root', 'root', 'test123', data[2][0])
wRTN.writer()

m.alert()