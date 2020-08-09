# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/4/1
from rest import REST
import datetime
import requests
import csv
from functools import reduce
import smtplib
import time
from email.mime.text import MIMEText


class modemPointsReader(object):
    def __init__(self,platformName,platformip,username,password,measurement,FWD,RTN):
        self.platformip = platformip
        self.platformName = platformName
        self.username = username
        self.password = password
        self.measurement = measurement
        self.FWD = FWD
        self.RTN = RTN
    def GetPerformanceUrls(self):
        try:
            rest = REST(self.platformip, self.username, self.password)
            hubmodule = rest.GET('hub-module')
            hubmoduleName = hubmodule[0]['devicePools'][0]['hubModuleId']['name']
            satnetID = hubmodule[0]['devicePools'][0]['hpsId']
            hubModuleType = hubmodule[0]['hubModuleType']
        except IndexError or TypeError as e:
            hubmoduleName = hubmodule[0]['hubModules'][0]['devicePools'][0]['hubModuleId']['name']
        csvFilenames = list()
        now=datetime.datetime.utcnow()
        now = now - datetime.timedelta(seconds=600)
        csvFilenames.append('performance_%s%02i.csv' % (now.strftime('%Y%m%d%H'), now.minute - now.minute % 5))
        csvFilenames.reverse()
        urls = list()
        url = '/remote-gui/%s/HMGW-0-0/mc/performance/' % hubmoduleName
        for filename in csvFilenames:
            urls.append(url + filename)
        return "http://" + self.platformip + urls[0]

    def getTerminalDict(self):
        url = self.GetPerformanceUrls()
        auth1 = (self.username, self.password)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        response = requests.get(url, auth=auth1, headers=headers, timeout=400)
        performanceDict = csv.DictReader(response.text.splitlines())
        return performanceDict

    def getPoints(self):
        date = self.GetPerformanceUrls().split('_')[-1].split('.')[0]
        now = date[0:4] + '-' + date[4:6] + '-' + date[6:8] + ' ' + date[8:10] + ':' + date[10:12] + ':00'
        rest = REST(self.platformip, self.username, self.password)
        pointList= list()
        forwardTotalList = []
        returnTotalList = []
        for row in self.getTerminalDict():
            print(row)
            modems = rest.GET('modem' + "/" + row['Modem id'], timeout=600)
            try:
                satnetID = modems['satelliteNetworkConfigurations'][0]['satelliteNetworkId']['name']
            except TypeError as e:
                satnetID = modems['attachment']['satelliteNetworkId']['name']
            modem = modems['id']['name']
            fields = {"Return throughput RT1": self.floadtoString(row["Return throughput RT1"]),
                      "Forward throughput RT3": self.floadtoString(row["Forward throughput RT3"]),
                      "Return throughput RT2": self.floadtoString(row["Return throughput RT2"]),
                      "Forward throughput CD2": self.floadtoString(row["Forward throughput CD2"]),
                      "Forward throughput BE": self.floadtoString(row["Forward throughput BE"]),
                      "Return throughput BE": self.floadtoString(row["Return throughput BE"]),
                      "Return throughput CD2": self.floadtoString(row["Return throughput CD2"]),
                      "Forward Es/N0 minimum": self.floadtoString(row["Forward Es/N0 minimum"]),
                      "Return throughput CD3": self.floadtoString(row["Return throughput CD3"]),
                      "Forward throughput RT2": self.floadtoString(row["Forward throughput RT2"]),
                      "Return C/N0 average": self.floadtoString(row["Return C/N0 average"]),
                      "Forward Es/N0 maximum": self.floadtoString(row["Forward Es/N0 maximum"]),
                      "Forward throughput CD1": self.floadtoString(row["Forward throughput CD1"]),
                      "Forward throughput RT1": self.floadtoString(row["Forward throughput RT1"]),
                      "Return throughput CD1": self.floadtoString(row["Return throughput CD1"]),
                      "Forward Es/N0 average": self.floadtoString(row["Forward Es/N0 average"]),
                      "Modem id": row["Forward throughput RT3"],
                      "Return C/N0 maximum": self.floadtoString(row["Return C/N0 maximum"]),
                      "Return throughput RT3": self.floadtoString(row["Return throughput RT3"]),
                      "Forward throughput CD3": self.floadtoString(row["Forward throughput CD3"]),
                      "Return C/N0 minimum": self.floadtoString(row["Return C/N0 minimum"])}
            pointList.append(
                {'fields': fields, 'measurement': self.measurement, 'tags': {'platform': self.platformName, 'satnet': satnetID,'modem':modem},
                 'time': now})
            qos = ['CD1','CD2','CD3','RT1','RT2','RT3','BE']
            forwardModem = 0.0
            returnModem = 0.0
            for i in qos:
                forwardModem += self.floadtoString(row['Forward throughput '+i])
                returnModem += self.floadtoString(row['Return throughput '+i])
            forwardTotalList.append(forwardModem)
            returnTotalList.append(returnModem)
        if len(forwardTotalList):
            forwardTotal = reduce(self.mySum,forwardTotalList)
        else:
            forwardTotal = 0
        if len(returnTotalList):
            returnTotal = reduce(self.mySum,returnTotalList)
        else:
            returnTotal = 0
        print(returnTotal)
        FWD = list()
        RTN = list()
        fieldsFWD = {'FWD':int(forwardTotal)}
        fieldsRTN = {'RTN':int(returnTotal)}
        FWD.append({'fields': fieldsFWD, 'measurement': self.FWD, 'tags': {'platform': self.platformName},'time': now})
        RTN.append({'fields': fieldsRTN, 'measurement': self.RTN, 'tags': {'platform': self.platformName},'time': now})
        return pointList, FWD ,RTN,forwardTotal,returnTotal

    def mySum(self,x, y):
        return x + y

    def floadtoString(self,str):
        if str:
            float(str)
        else:
            str = 0.0
        return float(str)

    def alert(self):
        SMTPServer = "smtp.126.com"
        Sender = "victor0731@126.com"
        receiver = "zwen@idirect.net,victor0731@126.com"
        passwd = "0123456789a"
        if self.getPoints()[3] <= 1:
            messageFWD = "Forward traffic outage at platform %s ,please check http://%s/cms" % (self.platformName,self.platformip)
            msg1 = MIMEText(messageFWD)
            msg1["Subject"] = "Forward traffic outage at platform %s ,please check http://%s/cms" % (self.platformName,self.platformip)
            msg1["From"] = Sender
            msg1["To"] = receiver
            mailServer = smtplib.SMTP(SMTPServer, 25)
            mailServer.login(Sender, passwd)
            mailServer.sendmail(Sender, [receiver], msg1.as_string())
            mailServer.quit()
        if self.getPoints()[4] <= 1:
            messageRTN = "Return traffic outage at platform %s ,please check http://%s/cms" % (self.platformName,self.platformip)
            msg2 = MIMEText(messageRTN)
            msg2["Subject"] = "Return traffic outage at platform %s ,please check http://%s/cms" % (self.platformName,self.platformip)
            msg2["From"] = Sender
            msg2["To"] = receiver
            mailServer = smtplib.SMTP(SMTPServer, 25)
            mailServer.login(Sender, passwd)
            mailServer.sendmail(Sender, [receiver], msg2.as_string())
            mailServer.quit()
