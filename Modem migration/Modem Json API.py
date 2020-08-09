# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/16

from rest import REST
import gevent
from gevent import monkey
monkey.patch_all(thread=False)
import logging
import csv
import re
import datetime
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

# http://10.255.0.91:16006/remote-gui/NRD_X01_ENCL-1/tcs-1-0/domain-15/terminal-18037/cgi-bin/index
class mobilityParser(object):
    def __init__(self,host,username,password):
        self.host = host
        self.username = username
        self.password = password
        self.HPS1 = [1,2,3,4,5,6]
        self.HPS2 = [8,9,10,11,12,13]
        self.HPS3 = [15,16,17,18,19,20]


    def gethubmodule(self):
        rest = REST(self.host, self.username, self.password)
        hubmodule = rest.GET('satellite-network/collect?property=beamId&property=hubProcessingSegmentId&property=certificationEnabled&property=id')
        return hubmodule

    def getModemCount(self):
        rest = REST(self.host, self.username, self.password)
        modemCount = rest.GET('modem/count')
        return modemCount

    def getModem(self,modemCount):
        logger.info("get all the terminal remote urls from NMS")
        rest = REST(self.host, self.username, self.password)
        modemCount = self.getModemCount()
        count =  modemCount['count']//100
        count1 = modemCount['count']%100
        urlList = []
        for i in range(count+1):
            start = (i * 100) +1
            if i == (count + 1):
                modem = rest.GET('modem?limit={}&start={}'.format((count1-1),start))
                urlList.append([(i['remoteGuiUrl'],i['macAddress'],i['id']['domainName'],i['id']['name'],i['locked']) for i in modem])
            else:
                modem = rest.GET('modem?limit=100&start={}'.format(start))
                urlList.append([(i['remoteGuiUrl'],i['macAddress'],i['id']['domainName'],i['id']['name'],i['locked']) for i in modem])
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
            else:
                logger.warn("response code is not 200 something wrong with getting parameter")
                pass
            return resData
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
        print(beamID)

        func = '{"FunctionName":"GetBeamData","Params":{"BeamId":%d}}'% beamID
        print(func)
        method = "GET"
        return self.sendRequest(url,func, method)

    def getActiveODUType(self,url):
        sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetActiveODUType", "SessionId": "' + sessionID + '" }'
        method = "GET"
        return self.sendRequest(url,func, method)

    def getODUTypeData(self,url):
        sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetODUTypeData","Params":{"ODUTypeId":1}, "SessionId": "' + sessionID + '" }'
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
        modemType = resData['RequestData']['System']['Desc']
        return modemType

    def writeToCSV(self,modemList):
        FILE = 'Mobilty Modem.csv'
        logger.info('Write to {}'.format(FILE))
        header = ['time', 'modem name', 'HPS', 'beamName','satnetName','VNO', 'hub module', 'ActiveBeamID', 'CF',
                  'SymbolRate']
        with open(FILE, 'a', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, header)
            dict_writer.writerows(modemList)

    def writeHeader(self):
        FILE = 'Mobilty Modem.csv'
        logger.info('Write to {}'.format(FILE))
        header = ['time', 'modem name', 'HPS','beamName','satnetName', 'VNO', 'hub module', 'ActiveBeamID', 'CF',
                  'SymbolRate']
        with open(FILE, 'a', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, header)
            dict_writer.writeheader()

    def terminalParser(self):
        a = mobilityParser(self.host, self.username, self.password)
        hubs = self.gethubmodule()
        print(hubs)
        count = a.getModemCount()
        res = a.getModem(count)
        print(res)
        self.writeHeader()
        now = datetime.datetime.utcnow().isoformat().split(".")[0]
        for modeminfoList in res:
            # print(modeminfoList)
            for modemList in modeminfoList:
                # print(modemList[-1])
                if not modemList[-1]:
                    macaddress = modemList[1]
                    url = modemList[0]
                    urlFinal = 'http://' + self.host + url + 'cgi-bin/cgiclient?request='
                    logger.info("trying to reach to modem remote gui=>{}".format(urlFinal))
                    VNO = modemList[2]
                    print(VNO)
                    modemName = modemList[3]
                    logger.info("get modem - {} parameter".format(modemName))
                    HPS = re.split('-',url)[4]
                    print(HPS)
                    a = re.split('/', url)[2].split("_")
                    hubmodule = a[0] + '_' + a[1]
                    print(hubmodule)
                    for hub in hubs:
                        if (hub['hubProcessingSegmentId']['name'].split(".")[-1].split("-")[-1] == HPS and hub['hubProcessingSegmentId']['name'].split(".")[0]) == hubmodule:
                            beamName = hub['beamId']['name']
                            print(beamName)
                            satnetName = hub['id']['name']
                            print(satnetName)
                    try:
                        activeBeamID = self.getActiveBeam(urlFinal)
                        beamData = self.getBeamData(activeBeamID,urlFinal)

                        if beamData['RequestData']['InitialCarrier1']['Enabled']:
                            centerFreq = beamData['RequestData']['InitialCarrier1']['Freq']
                            print(centerFreq)
                            SymbolRate = beamData['RequestData']['InitialCarrier1']['SymbolRate']
                            print(SymbolRate)
                        else:
                            centerFreq = beamData['RequestData']['InitialCarrier2']['Freq']
                            print(centerFreq)
                            SymbolRate = beamData['RequestData']['InitialCarrier2']['SymbolRate']
                            print(SymbolRate)
                        element = [{
                            "time": now,
                            "modem name": modemName,
                            "HPS": HPS,
                            "beamName" : beamName,
                            "satnetName" : satnetName,
                            'VNO': VNO,
                            "hub module": hubmodule,
                            "ActiveBeamID": activeBeamID,
                            "CF": centerFreq,
                            "SymbolRate": SymbolRate
                        }]

                        self.writeToCSV(element)
                    except Exception as e:
                        pass


class modemParser(object):
    def __init__(self,host,username,password,modemgroupIndex,modemData):
        self.modemgroupIndex = modemgroupIndex
        self.modemData = modemData
        self.host = host
        self.username = username
        self.password = password

    def gethubmodule(self):
        rest = REST(self.host, self.username, self.password)
        hubmodule = rest.GET(
            'satellite-network/collect?property=beamId&property=hubProcessingSegmentId&property=certificationEnabled&property=id')
        return hubmodule

    def terminalParser(self):
        hubs = self.gethubmodule()
        now = datetime.datetime.utcnow().isoformat().split(".")[0]
        for modemList in self.modemData[self.modemgroupIndex]:
            # print(modemList[-1])
            if not modemList[-1]:
                macaddress = modemList[1]
                url = modemList[0]
                urlFinal = 'http://' + self.host + url + 'cgi-bin/cgiclient?request='
                logger.info("trying to reach to modem remote gui=>{}".format(urlFinal))
                VNO = modemList[2]
                print(VNO)
                modemName = modemList[3]
                logger.info("get modem - {} parameter".format(modemName))
                HPS = re.split('-', url)[4]
                print(HPS)
                a = re.split('/', url)[2].split("_")
                hubmodule = a[0] + '_' + a[1]
                print(hubmodule)
                for hub in hubs:
                    if (hub['hubProcessingSegmentId']['name'].split(".")[-1].split("-")[-1] == HPS and
                        hub['hubProcessingSegmentId']['name'].split(".")[0]) == hubmodule:
                        beamName = hub['beamId']['name']
                        print(beamName)
                        satnetName = hub['id']['name']
                        print(satnetName)
                try:
                    activeBeamID = self.getActiveBeam(urlFinal)
                    beamData = self.getBeamData(activeBeamID, urlFinal)

                    if beamData['RequestData']['InitialCarrier1']['Enabled']:
                        centerFreq = beamData['RequestData']['InitialCarrier1']['Freq']
                        print(centerFreq)
                        SymbolRate = beamData['RequestData']['InitialCarrier1']['SymbolRate']
                        print(SymbolRate)
                    else:
                        centerFreq = beamData['RequestData']['InitialCarrier2']['Freq']
                        print(centerFreq)
                        SymbolRate = beamData['RequestData']['InitialCarrier2']['SymbolRate']
                        print(SymbolRate)
                    element = [{
                        "time": now,
                        "modem name": modemName,
                        "HPS": HPS,
                        "beamName": beamName,
                        "satnetName": satnetName,
                        'VNO': VNO,
                        "hub module": hubmodule,
                        "ActiveBeamID": activeBeamID,
                        "CF": centerFreq,
                        "SymbolRate": SymbolRate
                    }]

                    self.writeToCSV(element)
                except Exception as e:
                    pass


if __name__ == '__main__':
    host = '10.0.10.60'
    user = 'hno'
    password = '=kQ9+bQ(B+kh2NbD'
    a = mobilityParser(host,user,password)
    # count = a.getModemCount()
    # res = a.getModem(count)
    # print(res[0])
    # print(res[1])
    a.terminalParser()
