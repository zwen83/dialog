# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/7/2

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
import datetime
from bs4 import BeautifulSoup
import urllib.request
import time
import requests

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
class DialogAPI(object):
    def __init__(self,host,username,password):
        self.host = host
        self.username = username
        self.password = password

    def gethubmodule(self):
        rest = REST(self.host, self.username, self.password)
        hubmodule = rest.GET('satellite-network/collect?property=beamId&property=hubProcessingSegmentId&property=certificationEnabled&property=id')
        return hubmodule

    def getModemCount(self):
        rest = REST(self.host, self.username, self.password)
        modemCount = rest.GET('modem/count')
        return modemCount

    def getModem(self,macList):
        logger.info("get all the terminal remote urls from NMS")
        rest = REST(self.host, self.username, self.password)
        urlList = []
        for i in macList:
            modem = rest.GET('modem/mac-address/{}'.format(i))
            urlList.append([(modem['remoteGuiUrl'],modem['macAddress'],modem['id']['domainName'],modem['id']['name'],modem['locked'])])
        return urlList

    def sendRequest(self,url,func, method):
        # self.host = '192.168.2.99'  # as I am connected locally to the modem .. if you you are trying to access the modem from the hub then you will need a remote GUI URL
        if (method == "GET"):
            auth1 = (self.username, self.password)
            headers1 = {'Content-Type': '*/*',
                       'Accept': 'text/html'}
            res = requests.post(url=url, auth=auth1, headers=headers1)
            cookies = res.cookies
            result = requests.get(url + func,headers= headers1,cookies=cookies)
            # print(result)
            # print(type(result))
            if result.status_code == 200:
                resData = result.json()
                # print(resData)
                return resData
            else:
                logger.warn("response code is not 200 something wrong with getting parameter")
                pass

        if (method == "POST"):
            headers = {'TextId': 'request'}
            result = requests.post(url, data=func, headers=headers)
            if result.status_code == 200:
                return result
            else:
                pass
        else:
            logger.warn("unknown method !! \n")

    def authenticate(self,url):
        func = '{"FunctionName":"AuthenticatePassword","Params":{"LoginLevel":"expert","Password":"s3p"}}'
        method = "GET"
        resData = self.sendRequest(url,func, method)
        sessionID = resData['RequestData']['SessionId']
        # print("session ID: " + sessionID + '\n')
        return sessionID

    def getTemperatures(self,url):
        # sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetTemperatures"}'
        method = "GET"
        return self.sendRequest(url,func, method)

    def getActiveBeam(self,url):
        # sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetActiveBeam"}'
        method = "GET"
        return self.sendRequest(url,func, method)['RequestData']['ActiveBeamId']

    def getBeamData(self,beamID,url):
        func = '{"FunctionName":"GetBeamData","Params":{"BeamId":%d}}'% beamID
        method = "GET"
        return self.sendRequest(url,func, method)

    def getActiveODUType(self,url):
        sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetActiveODUType", "SessionId": "' + sessionID + '" }'
        method = "GET"
        return self.sendRequest(url,func, method)['RequestData']['ODUTypeId']

    def getODUTypeData(self,url,oduID):
        sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetODUTypeData","Params":{"ODUTypeId":%d}}'% oduID
        method = "GET"
        return self.sendRequest(url,func, method)

    def addBeam(self,url):
        sessionID = self.authenticate(url)
        func = {
            'request': '{"SessionId": "' + sessionID + '", "FunctionName":"AddBeam","Params": { "InitialCarrier1" : { "Freq" : 5000000000, "SymbolRate" : 10000000, "TSMode" : "dvbs2x", "Polarization"     : 0, "Enabled" : true }, "PointingCarrier1" : { "Carrier" : { "Freq" : 100000000000, "SymbolRate" : 100000000, "TSMode" : "dvbs2x", "Polarization" : 0, "Enabled" : true } }, "InitialCarrier2" : { "TimeSliceNumber" : 1, "Freq" : 0, "SymbolRate" : 0, "TSMode" : "dvbs2x", "Polarization" : 0, "Enabled" : false }, "PointingCarrier2" : { "Carrier" : { "TimeSliceNumber" : 1, "Freq" : 0, "SymbolRate" : 0, "TSMode" : "dvbs2x", "Polarization" : 0, "Enabled" : false } }, "PolarizationSkew" : 0, "OrbitalDegrees" : 0, "SatLatitudeVariance" : 0, "MaxSkew" : 0, "DefaultInitialCarrier" : 1, "DefaultPointingCarrier" : 1, "Hemisphere" : "east", "TxPolarization" : 0, "AcuXString" : "", "BeamName" : "", "Cost" : 0, "AutomaticPointingTimeout" : 210000, "GxtFileName" : "", "ExclusionZones" : [  ], "BeamId" : 99 }}'}
        method = "POST"
        return self.sendRequest(url,func, method)

    def getSwVersion(self,url):
        func = '{"FunctionName":"GetDeviceInformation"}'
        method = "GET"
        resData = self.sendRequest(url,func, method)  # This will return bunch of information from the modem
        swVersion = resData['RequestData']['Software']['CurrentVersion']  # You can parse the response so you get what you want, in this case I am getting the current SW version
        print('getSwVersion: ' + swVersion + '\n')
        return swVersion

    def getMonitoringData(self,url):
        func = '{"FunctionName":"GetMonitoringData"}'
        method = "GET"
        resData = self.sendRequest(url,func, method)
        return resData




