# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/4/2

from rest import REST
import datetime
import requests
import json
import csv
from functools import reduce
import smtplib
import time
from email.mime.text import MIMEText


class HRCpointsReader(object):
    def __init__(self,platformName,platformip,username,password,measurement):
        self.platformip = platformip
        self.platformName = platformName
        self.username = username
        self.password = password
        self.measurement = measurement


    def getHRCPoints(self):
        rest = REST(self.platformip, self.username, self.password)
        HPScount = rest.GET('satellite-network/count')['count']
        satnets = rest.GET('satellite-network')
        HRCRCGcount = 	rest.GET('/hrc-mxdma-return-capacity-group/count')['count']

        HRCRCG = rest.GET('hrc-mxdma-return-capacity-group')
        now = datetime.datetime.utcnow().isoformat()
        pointList = list()
        for satnetID in range(HPScount):
            try:
                hubmoduleName= satnets[satnetID]['hubProcessingSegmentId']['name'].split(".")[0]
            except KeyError as e:
                hubmoduleName = satnets[satnetID]['physicalSatnetId']['name'].split(".")[0]
            if self.platformName == 'AJN':
                url = 'http://%s/remote-gui/%s/HMGW-0/hrccontroller-%s/statistics' % (self.platformip, hubmoduleName, satnetID + 1)
            else:
                url = 'http://%s/remote-gui/%s/HMGW-0-0/hrccontroller-%s/statistics' % (self.platformip,hubmoduleName, satnetID+1)
            print(url)
            auth1 = (self.username, self.password)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
            try:
                response = requests.get(url, auth=auth1, headers=headers, timeout=400)
            except Exception as q:
                pass
            try:
                if response.status_code == 200:
                    performance = json.loads(response.text)
                    satnetName = satnets[satnetID]['id']['name']
                    for i in range(HRCRCGcount):
                        HRCSYSID = HRCRCG[i]['id']['systemId']
                        HRCRCGsatnet = HRCRCG[i]['satelliteNetworkId']['name']
                        if satnetName == HRCRCGsatnet:
                            RCGdata = performance['carrierGroups']['hrc_mxdma_rcg_'+str(HRCSYSID)]
                            fields = {'allocatedRate':self.floadtoString(RCGdata['allocatedRate']['value']) ,
                                      'loggedOnTerminals':self.floadtoString(RCGdata['loggedOnTerminals']),
                                      'usedBandwidth':self.floadtoString(RCGdata['usedBandwidth']),
                                      'physicalLayerEfficiency' :self.floadtoString(RCGdata['physicalLayerEfficiency']),
                                      'bestModcodEfficiency' :self.floadtoString(RCGdata['bestModcodEfficiency'])
                                      }
                            pointList.append(
                                {'fields': fields, 'measurement': self.measurement,
                                 'tags': {'platform': self.platformName, 'satnet': satnetName,'MxDMA-RCG':RCGdata['name']},
                                 'time': now})
            except UnboundLocalError as e:
                pass
        return pointList

    def floadtoString(self,str):
        if str:
            float(str)
        else:
            str = 0.0
        return float(str)






