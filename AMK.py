# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/4/3

from modemPointsReader import modemPointsReader
from influxWriter import influxWriter
from HRCpointsReader import HRCpointsReader
from CPMpointsReader import CPMpointsReader
import threading
import rest


m = modemPointsReader('AMK', '10.255.0.83:55006', 'hno', 'D!@10g', 'modemKPIs', 'forwardTotal', 'returnTotal')

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