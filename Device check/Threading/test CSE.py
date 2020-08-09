# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/26

import time
import threading
import logging
import copy
import json
import csv
from pathlib import Path
import re
import requests
import datetime
from bs4 import BeautifulSoup
import urllib.request


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fh = logging.FileHandler(__name__+'.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)
# Edit here to match the SN name. Note that for BHI, it ends with e.g. SN1, but JAV ends with SN-1
logging.getLogger('rest').setLevel(logging.DEBUG)



class kacific(threading.Thread):
    def __init__(self,ip,hub_name):
        super().__init__()
        self.hub_name = hub_name
        self.ip = ip
        self.HPS1 = [1,2,3,4,5,6]
        self.HPS2 = [8,9,10,11,12,13]
        self.HPS3 = [15,16,17,18,19,20]
        self.enclosure = [1,2,3]
        self.allData = []

    def run(self):
        self.gettotalpersatnet()
        logger.info("running thread - {}".format(self.name))

    def gettotalpersatnet(self):
        FILE = 'CSE_result_{}.csv'.format(self.hub_name)

        for enclosureID in self.enclosure:
            if enclosureID == 1:

                for x in self.HPS1:
                    try:
                        urlcse1 = r"http://{}/remote-gui/{}_ENCL-1/CSE-{}/tc-shape-server/www/group_table.html".format(self.ip,self.hub_name,x)
                        cse1= self.readCSEHTML(urlcse1,self.hub_name,x)
                        urldcp1 = r"http://{}/remote-gui/{}_ENCL-1/DCP-{}/tc-shape-server/www/group_table.html".format(self.ip,self.hub_name,x)
                        dcp1 = self.readDCPHTML(urldcp1,self.hub_name,x)
                        Merge1 = cse1.copy()
                        Merge1.update(dcp1)
                        self.allData.append(Merge1)
                    except Exception as e:
                        print(e)
                        pass

            elif enclosureID == 2:
                for y in self.HPS2:
                    try:
                        urlcse2 = r"http://{}/remote-gui/{}_ENCL-2/CSE-{}/tc-shape-server/www/group_table.html".format(self.ip,self.hub_name,y)
                        cse2 = self.readCSEHTML(urlcse2,self.hub_name,y)
                        urldcp2 = r"http://{}/remote-gui/{}_ENCL-2/DCP-{}/tc-shape-server/www/group_table.html".format(self.ip,self.hub_name,y)
                        dcp2 = self.readDCPHTML(urldcp2,self.hub_name,y)
                        Merge2 = cse2.copy()
                        Merge2.update(dcp2)
                        self.allData.append(Merge2)
                    except Exception as e:
                        print(e)
                        pass

            elif enclosureID == 3:
                for z in self.HPS3:
                    try:
                        urlcse3 = r"http://{}/remote-gui/{}_ENCL-3/CSE-{}/tc-shape-server/www/group_table.html".format(self.ip,self.hub_name,z)
                        cse3 = self.readCSEHTML(urlcse3,self.hub_name,z)
                        urldcp2 = r"http://{}/remote-gui/{}_ENCL-3/DCP-{}/tc-shape-server/www/group_table.html".format(self.ip,self.hub_name,z)
                        dcp3 = self.readDCPHTML(urldcp2,self.hub_name,z)
                        Merge3 = cse3.copy()
                        Merge3.update(dcp3)
                        self.allData.append(Merge3)
                    except Exception as e:
                        print(e)
                        pass

        if len(self.allData) > 0:
            logger.info('Write to {}'.format(FILE))
            header = ['time', 'Hub Name', 'Satnet', 'FWD Total bitrate', 'FWD Drop bitrate','RTN Total bitrate','RTN Drop bitrate']
            with open(FILE, 'w', newline="") as output_file:
                dict_writer = csv.DictWriter(output_file, header)
                dict_writer.writeheader()
                dict_writer.writerows(self.allData)
        print(self.allData)
        return self.allData

# http://10.0.10.60/remote-gui/KAC_SUB-1_ENCL-1/DCP-2/tc-shape-server/www/group_table.html
# http://10.255.0.63/remote-gui/KAC_BHI-1_ENCL-3/CSE-19/tc-shape-server/www/group_table.html

    def readDCPHTML(self, url, gwName, HPSid):
        now = datetime.datetime.utcnow().isoformat()
        auth1 = ("hno", "D!@10g")
        headers = {'Content-Type': '*/*',
                   'Accept': 'text/html'}
        res = requests.post(url=url, auth=auth1, headers=headers)
        cookies = res.cookies
        res1 = requests.get(url=url, auth=auth1, headers=headers, cookies=cookies)
        logger.info("getting DCP info from {}".format(url))
        soup = BeautifulSoup(res1.text, 'lxml')
        data1 = soup.font.contents[-1]
        data2 = str(data1)
        patdcp = r'"right">(.*?) bits/s</td>'
        dataDCPrate = re.compile(patdcp)
        data = dataDCPrate.findall(data2)
        dcptotalrate = data[4].split(",")
        dcpdroprate = data[2].split(",")
        # print(dcptotalrate)
        total = ''
        for i in dcptotalrate:
            total += i
        dcpTotalRate = int(total)
        total1 = ''
        for i in dcpdroprate:
            total1 += i
        dcpDropRate = int(total1)
        # print(dcpTotalRate)
        # print(dcpDropRate)
        element = {
            "RTN Total bitrate": dcpTotalRate,
            "RTN Drop bitrate": dcpDropRate
        }
        return element


    def readCSEHTML(self,url,gwName,HPSid):
        now = datetime.datetime.utcnow().isoformat()
        auth1 = ("hno", "D!@10g")
        headers = {'Content-Type': '*/*',
                   'Accept': 'text/html'}
        res = requests.post(url=url, auth=auth1, headers=headers)
        cookies = res.cookies
        res1 = requests.get(url=url, auth=auth1, headers=headers, cookies=cookies)
        logger.info("getting CSE info from {}".format(url))
        data2 = res1.text
        pat1 = r'<tr><td colspan="18">(.*?)ms</td></tr>'
        DataUrl = re.compile(pat1)
        dataLink = DataUrl.findall(data2)

        pat2 = r'align="right">(.*?)&nbsp;bits/s'
        Data = re.compile(pat2)
        dataValue1 = Data.findall(dataLink[0])
        totalBeamValue = dataValue1[-1].split(",")
        totalBeamDropValue = dataValue1[-3].split(",")
        total = ''
        for i in totalBeamValue:
            total += i
        totalValue = int(total)
        totaldrop = ''
        for i in totalBeamDropValue:
            totaldrop += i
        totalValueDrop = int(totaldrop)

        element = {
            "time" : now,
            "Hub Name": gwName,
            "Satnet": HPSid,
            "FWD Total bitrate": totalValue,
            "FWD Drop bitrate": totalValueDrop
        }
        print(element)
        return element

if __name__ == '__main__':

    start = time.time()
    ip = '10.255.0.63'
    kacific1 =  kacific(ip,'KAC_JAV-1')
    kacific1.start()

    kacific2 =  kacific(ip,'KAC_SUB-2')
    kacific2.start()

    kacific3 =  kacific(ip,'KAC_SUB-1')
    kacific3.start()

    kacific4 =  kacific(ip,'KAC_JAV-2')
    kacific4.start()

    kacific5 =  kacific(ip,'KAC_BHI-1')
    kacific5.start()

    kacific6 =  kacific(ip,'KAC_BHI-2')
    kacific6.start()
    end = time.time()
    print("total time is %0.2f" % (end - start))


