# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/4/1

from modemPointsReader import modemPointsReader
from influxWriter import influxWriter
from HRCpointsReader import HRCpointsReader
from CPMpointsReader import CPMpointsReader
import threading
import rest




'''
get HRC KPIs

'''
def HRC():
    platformList = {'AMI': '192.168.48.126:36006',
                    'BCnet': '192.168.48.125:35006',
                    'Bambu': '192.168.48.131:41006',
                    'infokom1': '192.168.48.128:38006',
                    'infokom2': '192.168.48.129:39006',
                    'patrakom': '10.255.0.99:24006',
                    'PSN2': '192.168.48.132:42006',
                    'skyreach': '192.168.48.134:44006',
                    'PSN1': '192.168.48.133:43006',
                    'Telered': '192.168.48.130:40006',
                    'TNIC': '192.168.48.136:46006',
                    'TNIK': '192.168.48.137:47006',
                    'Stella': '10.255.0.100:25006',
                    'AMK' : '10.255.0.83:55006',
                    'satsol': '10.255.0.47:47006',
                    'speedcast': '192.168.48.127:37006'
                    }

    for name , ip in platformList.items():
        print(name)
        h = HRCpointsReader(name, ip,'hno','D!@10g','HRCKPIs')
        try:
            for hrcrow in h.getHRCPoints():
                print(hrcrow)
                wHRC = influxWriter('192.168.48.42','root','root','test123',hrcrow)
                wHRC.writer()
        except rest.ConnectionError as e:
            pass
    timer = threading.Timer(600, HRC)
    timer.start()
    timer.join()

'''
get 4CPM KPIs

'''
def CPM():
    platformList = {'AMI': '192.168.48.126:36006',
                    'BCnet': '192.168.48.125:35006',
                    'Bambu': '192.168.48.131:41006',
                    'infokom1': '192.168.48.128:38006',
                    'infokom2': '192.168.48.129:39006',
                    'patrakom': '10.255.0.99:24006',
                    'PSN2': '192.168.48.132:42006',
                    'PSN1': '192.168.48.133:43006' ,
                    'skyreach': '192.168.48.134:44006',
                    'Telered': '192.168.48.130:40006',
                    'TNIC': '192.168.48.136:46006',
                    'TNIK': '192.168.48.137:47006',
                    'Stella': '10.255.0.100:25006',
                    'AMK' : '10.255.0.83:55006',
                    'AJN' : '192.168.48.42:22013',
                    'ABS1' : '192.168.48.42:17013',
                    'satsol':'10.255.0.47:47006',
                    'speedcast':'192.168.48.127:37006'}

    # 'MonVSAT': '192.168.48.42:25013'
    for name , ip in platformList.items():
        print(name)
        C = CPMpointsReader(name,ip,'hno','D!@10g','CPMKPIs')
        try:
            for cpmrow in C.getCPMPoints():
                print(cpmrow)
                wCPM = influxWriter('192.168.48.42','root','root','test123',cpmrow)
                wCPM.writer()
        except rest.ConnectionError as e:
            pass
        except NameError as e:
            pass
    timer = threading.Timer(600, CPM)
    timer.start()
    timer.join(1)


if __name__ == "__main__":

    cpm = threading.Thread(target=CPM)
    cpm.start()

    hrc = threading.Thread(target=HRC)
    hrc.start()








