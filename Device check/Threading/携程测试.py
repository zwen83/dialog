# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/28
from greenlet import greenlet
from rest import REST
import gevent
from gevent import monkey
monkey.patch_all(thread=False)
import multiprocessing
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
import time

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

class kacific(object):
    def __init__(self,ip,hub_name):
        self.hub_name = hub_name
        self.ip = ip
        self.HPS1 = [1,2,3,4,5,6]
        self.HPS2 = [8,9,10,11,12,13]
        self.HPS3 = [15,16,17,18,19,20]
        self.enclosure = [1,2,3]
        self.allData = []
        rest = REST(self.ip, 'hno', 'D!@10g')
        self.json = rest.GET('satellite-network/collect?property=beamId&property=hubProcessingSegmentId')


    def Satnet1(self):
        for x in self.HPS1:
            try:
                for hps in self.json:
                    if (hps['hubProcessingSegmentId']['name'].split(".")[1].split("-")[1] == str(x)) and (hps['hubProcessingSegmentId']['name'].split(".")[0] == self.hub_name):
                        beamID = hps['beamId']['name']

                        urlcse1 = r"http://{}/remote-gui/{}_ENCL-1/CSE-{}/tc-shape-server/www/group_table.html".format(self.ip,self.hub_name,x)
                        cse1= self.readCSEHTML(urlcse1,self.hub_name,x,beamID)
                        gevent.sleep(0.1)
                        urldcp1 = r"http://{}/remote-gui/{}_ENCL-1/DCP-{}/tc-shape-server/www/group_table.html".format(self.ip,self.hub_name,x)
                        dcp1 = self.readDCPHTML(urldcp1,self.hub_name,x)
                        gevent.sleep(0.1)
                        Merge1 = cse1.copy()
                        Merge1.update(dcp1)
                        self.allData.append(Merge1)
                        gevent.sleep(0.1)
            except Exception as e:
                print(e)
                pass

    def Satnet2(self):
        for y in self.HPS2:
            try:
                for hps in self.json:
                    if (hps['hubProcessingSegmentId']['name'].split(".")[1].split("-")[1] == str(y)) and (hps['hubProcessingSegmentId']['name'].split(".")[0] == self.hub_name):
                        beamID = hps['beamId']['name']

                        urlcse2 = r"http://{}/remote-gui/{}_ENCL-2/CSE-{}/tc-shape-server/www/group_table.html".format(self.ip,self.hub_name,
                                                                                                                       y)
                        cse2 = self.readCSEHTML(urlcse2, self.hub_name, y,beamID)
                        gevent.sleep(0.1)
                        urldcp2 = r"http://{}/remote-gui/{}_ENCL-2/DCP-{}/tc-shape-server/www/group_table.html".format(self.ip,
                                                                                                                       self.hub_name,
                                                                                                                       y)
                        dcp2 = self.readDCPHTML(urldcp2, self.hub_name, y)
                        gevent.sleep(0.1)
                        Merge2 = cse2.copy()
                        Merge2.update(dcp2)
                        self.allData.append(Merge2)
                        gevent.sleep(0.1)

            except Exception as e:
                print(e)
                pass

    def Satnet3(self):
        for z in self.HPS3:
            try:
                for hps in self.json:
                    if (hps['hubProcessingSegmentId']['name'].split(".")[1].split("-")[1] == str(z)) and (hps['hubProcessingSegmentId']['name'].split(".")[0] == self.hub_name):
                        beamID = hps['beamId']['name']
                        urlcse3 = r"http://{}/remote-gui/{}_ENCL-3/CSE-{}/tc-shape-server/www/group_table.html".format(self.ip,
                                                                                                                       self.hub_name,
                                                                                                                       z)
                        cse3 = self.readCSEHTML(urlcse3, self.hub_name, z,beamID)
                        gevent.sleep(0.1)
                        urldcp2 = r"http://{}/remote-gui/{}_ENCL-3/DCP-{}/tc-shape-server/www/group_table.html".format(self.ip,
                                                                                                                       self.hub_name,
                                                                                                                       z)
                        dcp3 = self.readDCPHTML(urldcp2, self.hub_name, z)
                        gevent.sleep(0.1)
                        Merge3 = cse3.copy()
                        Merge3.update(dcp3)
                        self.allData.append(Merge3)
                        gevent.sleep(0.1)
                        print(self.allData)
            except Exception as e:
                print(e)
                pass


    def gettotalpersatnet(self):
        print("{}-------running".format(multiprocessing.current_process()))
        FILE = 'Throughput_{}.csv'.format(self.hub_name)
        g1 = gevent.spawn(self.Satnet1)
        g2 = gevent.spawn(self.Satnet2)
        g3 = gevent.spawn(self.Satnet3)
        gevent.joinall([
            g1,g2,g3
        ])

        if len(self.allData) > 0:
            logger.info('Write to {}'.format(FILE))
            header = ['time', 'Hub Name','Beam ID', 'Satnet', 'FWD Total bitrate', 'FWD Drop bitrate','RTN Total bitrate','RTN Drop bitrate']
            with open(FILE, 'w', newline="") as output_file:
                dict_writer = csv.DictWriter(output_file, header)
                dict_writer.writeheader()
                dict_writer.writerows(self.allData)
        print(self.allData)
        print(type(self.allData))
        # queue.put(self.allData)
        logger.info("put ------- {} into queue".format(self.allData))

        return self.allData




    # def writer(self):
    #     data = self.gettotalpersatnet()
    #     FILE = 'Throughput.csv'
    #     with open(FILE, 'a+', newline="") as output_file:
    #         dict_writer = csv.DictWriter(output_file, header)
    #         dict_writer.writeheader()
    #         dict_writer.writerows(data)



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


    def readCSEHTML(self,url,gwName,HPSid,beamID):
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
            "FWD Drop bitrate": totalValueDrop,
            "Beam ID" : beamID
        }
        print(element)
        return element

def readQueue(queue):
    while True:
        if queue.qsize != 0:
            dict1 = queue.pop()
        else:
            break
        return dict1


def multi():
    ip = '10.255.0.63'
    # queue  = multiprocessing.Manager().Queue(6)
    kacific1 =  kacific(ip,'KAC_JAV-1')
    kacific2 =  kacific(ip,'KAC_JAV-2')
    kacific3 =  kacific(ip,'KAC_SUB-1')
    kacific4 =  kacific(ip,'KAC_SUB-2')
    kacific5 =  kacific(ip,'KAC_BHI-1')
    kacific6 =  kacific(ip,'KAC_BHI-2')
    # pp.apply_async(kacific1.gettotalpersatnet,(queue,))
    # pp.apply_async(kacific2.gettotalpersatnet,(queue,))
    # pp.apply_async(kacific3.gettotalpersatnet,(queue,))
    # pp.apply_async(kacific4.gettotalpersatnet,(queue,))
    # pp.apply_async(kacific5.gettotalpersatnet,(queue,))
    # pp.apply_async(kacific6.gettotalpersatnet,(queue,))
    # allData = pp.apply_async(readQueue,(queue,))
    a = multiprocessing.Process(target=kacific1.gettotalpersatnet)
    b = multiprocessing.Process(target=kacific2.gettotalpersatnet)
    c = multiprocessing.Process(target=kacific3.gettotalpersatnet)
    d = multiprocessing.Process(target=kacific4.gettotalpersatnet)
    e = multiprocessing.Process(target=kacific5.gettotalpersatnet)
    f = multiprocessing.Process(target=kacific6.gettotalpersatnet)
    a.start()
    b.start()
    c.start()
    d.start()
    e.start()
    f.start()

    # pp.close()
    # pp.join()
    allData = []
    allData.append(a)
    allData.append(b)
    allData.append(c)
    allData.append(d)
    allData.append(e)
    allData.append(f)
    return allData


if __name__ == '__main__':
    start = time.time()
    # pp = multiprocessing.Pool(6)
    allData = multi()
    print(allData)

    # header = ['time', 'Hub Name', 'Satnet', 'FWD Total bitrate', 'FWD Drop bitrate', 'RTN Total bitrate',
    #           'RTN Drop bitrate']
    # FILE = 'Throughput.csv'

    # allData = kacific1.allData + kacific2.allData + kacific3.allData + kacific4.allData + kacific5.allData + kacific6.allData

    # with open(FILE, 'w', newline="") as output_file:
    #     dict_writer = csv.DictWriter(output_file, header)
    #     dict_writer.writeheader()
    #     dict_writer.writerows(allData)
    # end = time.time()
    # print("total time is %0.2f" % (end - start))





