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

class CPMpointsReader(object):
    def __init__(self,platformName,platformip,username,password,measurement):
        self.platformip = platformip
        self.platformName = platformName
        self.username = username
        self.password = password
        self.measurement = measurement



    def GetHubmodules(self):
        global logger
        hubmodules = None
        rest = REST(self.platformip, self.username, self.password)
        try:
            hubmodules = rest.GET('hub-module/collect?property=id&property=locked&property=hubModuleType&property=enclosures&property=physicalSatNets')
        except:
            logger.exception('Exception while fetching hubmodule info:')
        return hubmodules

    def getCPMPoints(self):
        now = datetime.datetime.utcnow().isoformat()
        pointList = list()
        for hm in self.GetHubmodules():
            if 'locked' in hm and hm['locked']:
                continue
            if 'physicalSatNets' in hm:
                for sn in hm['physicalSatNets']:
                    if 'hubModuleType' in hm:
                        for i in range(1,5):
                            url = 'http://%s/remote-gui/%s/cpmctl-%i/amp%i/stats/amp' % (self.platformip,hm['id']['name'], sn['hpsId'] if 'hpsId' in sn else sn['if'], i)
                            auth1 = (self.username, self.password)
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
                            try:

                                response = requests.get(url, auth=auth1, headers=headers, timeout=400)
                            except requests.exceptions.ConnectionError as q:
                                pass
                            if response.status_code == 200:
                                try:
                                    performance = json.loads(response.text)
                                except json.decoder.JSONDecodeError as e:
                                    pass
                                fields = {'Loggedon_sits' : self.floadtoString(performance['Loggedon_sits']),
                                          'prov_sits' : self.floadtoString(performance['prov_sits'])
                                          }
                                pointList.append(
                                    {'fields': fields, 'measurement': self.measurement,
                                     'tags': {'platform': self.platformName, 'satnet': sn['hpsId'] if 'hpsId' in sn else sn['if'],
                                              'AMP': 'AMP'+ str(i)},
                                     'time': now})

        return pointList

    def floadtoString(self,str):
        if str:
            float(str)
        else:
            str = 0.0
        return float(str)
