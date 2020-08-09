# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/20


# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/16

from rest import REST
import gevent
from gevent import monkey

monkey.patch_all(thread=False)
import multiprocessing
import threading
import logging
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
fh = logging.FileHandler(__name__ + '.log')
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
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.HPS1 = [1, 2, 3, 4, 5, 6]
        self.HPS2 = [8, 9, 10, 11, 12, 13]
        self.HPS3 = [15, 16, 17, 18, 19, 20]

    '''
    REST call methods
    '''

    def gethubmodule(self):
        rest = REST(self.host, self.username, self.password)
        hubmodule = rest.GET(
            'satellite-network/collect?property=beamId&property=hubProcessingSegmentId&property=certificationEnabled&property=id')
        return hubmodule

    def getModemCount(self):
        rest = REST(self.host, self.username, self.password)
        modemCount = rest.GET('modem/count')
        return modemCount

    '''
    divided all the modems into groups, 100 terminals per group
    '''

    def getModem(self, modemCount):
        logger.info("get all the terminal remote urls from NMS")
        rest = REST(self.host, self.username, self.password)
        modemCount = self.getModemCount()
        count = modemCount['count'] // 100
        count1 = modemCount['count'] % 100
        urlList = []
        for i in range(count + 1):
            start = (i * 100) + 1
            if i == (count + 1):
                modem = rest.GET('modem?limit={}&start={}'.format((count1 - 1), start))
                urlList.append(
                    [(i['remoteGuiUrl'], i['macAddress'], i['id']['domainName'], i['id']['name'], i['locked']) for i in
                     modem])
            else:
                modem = rest.GET('modem?limit=100&start={}'.format(start))
                urlList.append(
                    [(i['remoteGuiUrl'], i['macAddress'], i['id']['domainName'], i['id']['name'], i['locked']) for i in
                     modem])
        return urlList

    '''
    sent JSON request: GET or POST
    '''

    def sendRequest(self, url, func, method):
        if (method == "GET"):
            auth1 = (self.username, self.password)
            headers1 = {'Content-Type': '*/*',
                        'Accept': 'text/html'}
            res = requests.post(url=url, auth=auth1, headers=headers1)
            cookies = res.cookies
            result = requests.get(url + func, headers=headers1, cookies=cookies)
            if result.status_code == 200:
                resData = result.json()
                return resData
            else:
                logger.warn("the requested modem is not online")
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

    '''
    Specific POST JSON CALLS

    '''

    def addBeam(self, url):
        sessionID = self.authenticate(url)
        func = {
            'request': '{"SessionId": "' + sessionID + '", "FunctionName":"AddBeam","Params": { "InitialCarrier1" : { "Freq" : 5000000000, "SymbolRate" : 10000000, "TSMode" : "dvbs2x", "Polarization"     : 0, "Enabled" : true }, "PointingCarrier1" : { "Carrier" : { "Freq" : 100000000000, "SymbolRate" : 100000000, "TSMode" : "dvbs2x", "Polarization" : 0, "Enabled" : true } }, "InitialCarrier2" : { "TimeSliceNumber" : 1, "Freq" : 0, "SymbolRate" : 0, "TSMode" : "dvbs2x", "Polarization" : 0, "Enabled" : false }, "PointingCarrier2" : { "Carrier" : { "TimeSliceNumber" : 1, "Freq" : 0, "SymbolRate" : 0, "TSMode" : "dvbs2x", "Polarization" : 0, "Enabled" : false } }, "PolarizationSkew" : 0, "OrbitalDegrees" : 0, "SatLatitudeVariance" : 0, "MaxSkew" : 0, "DefaultInitialCarrier" : 1, "DefaultPointingCarrier" : 1, "Hemisphere" : "east", "TxPolarization" : 0, "AcuXString" : "", "BeamName" : "", "Cost" : 0, "AutomaticPointingTimeout" : 210000, "GxtFileName" : "", "ExclusionZones" : [  ], "BeamId" : 11 }}'}
        method = "POST"
        return self.sendRequest(url, func, method)

    '''
        Specific GET JSON CALLS
    '''

    def authenticate(self, url):
        func = '{"FunctionName":"AuthenticatePassword","Params":{"LoginLevel":"expert","Password":"s3p"}}'
        method = "GET"
        resData = self.sendRequest(url, func, method)
        sessionID = resData['RequestData']['SessionId']
        # print("session ID: " + sessionID + '\n')
        return sessionID

    def getTemperatures(self, url):
        # sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetTemperatures"}'
        method = "GET"
        return self.sendRequest(url, func, method)

    def getActiveBeam(self, url):
        # sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetActiveBeam"}'
        method = "GET"
        return self.sendRequest(url, func, method)['RequestData']['ActiveBeamId']

    def getBeamData(self, beamID, url):
        func = '{"FunctionName":"GetBeamData","Params":{"BeamId":%d}}' % beamID
        method = "GET"
        return self.sendRequest(url, func, method)

    def getActiveODUType(self, url):
        sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetActiveODUType", "SessionId": "' + sessionID + '" }'
        method = "GET"
        return self.sendRequest(url, func, method)['RequestData']['ODUTypeId']

    def getODUTypeData(self, url, oduID):
        sessionID = self.authenticate(url)
        func = '{ "FunctionName": "GetODUTypeData","Params":{"ODUTypeId":%d}}' % oduID
        method = "GET"
        return self.sendRequest(url, func, method)

    def getSwVersion(self, url):
        func = '{"FunctionName":"GetDeviceInformation"}'
        method = "GET"
        resData = self.sendRequest(url, func, method)  # This will return bunch of information from the modem
        swVersion = resData['RequestData']['Software'][
            'CurrentVersion']  # You can parse the response so you get what you want, in this case I am getting the current SW version
        return swVersion

    def getMonitoringData(self, url):
        func = '{"FunctionName":"GetMonitoringData"}'
        method = "GET"
        resData = self.sendRequest(url, func, method)
        return resData

    '''
    write headers and per modem data to CSV
    '''

    def writeToCSV(self, modemList):
        FILE = 'Mobilty Modem.csv'
        logger.info('Write modemlist - {} to {}'.format(modemList[0]['modem name'], FILE))
        header = ['time', 'modem name', 'modemType', 'macaddress', 'HPS', 'beamName', 'satnetName', 'VNO',
                  'ActiveBeamID', 'CF',
                  'SymbolRate', 'RXvoltage', 'ElevationOffset', 'LowBand_LO', 'HighBand_LO', 'BUC_LO', 'temperature',
                  'cpuUsage', 'forwardModcod', 'uptime', 'ESN0', 'ReceivePower', 'BE_RX', 'BE_TX', 'CD1_RX', 'CD1_TX',
                  'CD2_RX', 'CD2_TX', 'CD3_RX', 'CD3_TX', 'RT1_RX', 'RT1_TX', 'RT2_RX', 'RT2_TX', 'RT3_RX', 'RT3_TX']
        with open(FILE, 'a', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, header)
            dict_writer.writerows(modemList)

    def writeHeader(self):
        FILE = 'Mobilty Modem.csv'
        logger.info('Write CSV header to {}'.format(FILE))
        header = ['time', 'modem name', 'modemType', 'macaddress', 'HPS', 'beamName', 'satnetName', 'VNO',
                  'ActiveBeamID', 'CF',
                  'SymbolRate', 'RXvoltage', 'ElevationOffset', 'LowBand_LO', 'HighBand_LO', 'BUC_LO', 'temperature',
                  'cpuUsage', 'forwardModcod', 'uptime', 'ESN0', 'ReceivePower', 'BE_RX', 'BE_TX', 'CD1_RX', 'CD1_TX',
                  'CD2_RX', 'CD2_TX', 'CD3_RX', 'CD3_TX', 'RT1_RX', 'RT1_TX', 'RT2_RX', 'RT2_TX', 'RT3_RX', 'RT3_TX']
        with open(FILE, 'a', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, header)
            dict_writer.writeheader()

    '''
    main method to invoke all the above 
    1)     REST call to get the modem info,mapping with beam/satnet/HPS info
    2)     JSON call to get the remote modem info i.e. temperature,ODU,active beam...
    3)     generate a dict element, save into all the REST/JSON return parameters
    '''

    def terminalParser(self, modemList, hubs):
        now = datetime.datetime.utcnow().isoformat().split(".")[0]
        if not modemList[-1]:
            macaddress = modemList[1]
            url = modemList[0]
            urlFinal = 'http://' + self.host + url + 'cgi-bin/cgiclient?request='
            logger.info("trying to reach to modem remote gui=>{}".format(urlFinal))
            VNO = modemList[2]
            modemName = modemList[3]
            logger.info("get modem - {} parameter".format(modemName))
            HPS = re.split('-', url)[3]
            print(HPS)
            # a = re.split('/', url)[2].split("_")
            # hubmodule = a[0] + '_' + a[1]
            for hub in hubs:
                print(hub)
                print(hub['beamId']['name'])
                print(hub['id']['name'])
                if hub['hubProcessingSegmentId']['name'].split(".")[-1].split("-")[-1] == HPS:
                    beamName = hub['beamId']['name']
                    satnetName = hub['id']['name']
            try:
                activeBeamID = self.getActiveBeam(urlFinal)
                beamData = self.getBeamData(activeBeamID, urlFinal)
                MonitoringData = self.getMonitoringData(urlFinal)
                modemType = MonitoringData['RequestData']['System']['Desc']
                temperature = MonitoringData['RequestData']['Status']['Temp']
                cpuUsage = MonitoringData['RequestData']['Status']['CpuUsage'][0]
                forwardModcod = MonitoringData['RequestData']['Demods'][0]['Modcod']
                uptime = MonitoringData['RequestData']['System']['UpTime']
                ESN0 = MonitoringData['RequestData']['Demods'][0]['EsN0']
                ReceivePower = MonitoringData['RequestData']['Demods'][0]['RxPwr']
                ActiveODUType = self.getActiveODUType(urlFinal)
                ODUTypeData = self.getODUTypeData(urlFinal, ActiveODUType)
                RXvoltage = ODUTypeData['RequestData']['VoltageSelection']
                ElevationOffset = ODUTypeData['RequestData']['ElevationOffset']
                LowBand_LO = ODUTypeData['RequestData']['LowBand']['LO']
                HighBand_LO = ODUTypeData['RequestData']['HighBand']['LO']
                BUC_LO = ODUTypeData['RequestData']['BUCData']['LO']
                BE_RX = MonitoringData['RequestData']['Traffic'][8]['RtRxBitrate']
                BE_TX = MonitoringData['RequestData']['Traffic'][8]['RtTxBitrate']
                CD1_RX = MonitoringData['RequestData']['Traffic'][5]['RtTxBitrate']
                CD1_TX = MonitoringData['RequestData']['Traffic'][5]['RtTxBitrate']
                CD2_RX = MonitoringData['RequestData']['Traffic'][6]['RtTxBitrate']
                CD2_TX = MonitoringData['RequestData']['Traffic'][6]['RtTxBitrate']
                CD3_RX = MonitoringData['RequestData']['Traffic'][7]['RtTxBitrate']
                CD3_TX = MonitoringData['RequestData']['Traffic'][7]['RtTxBitrate']
                RT1_RX = MonitoringData['RequestData']['Traffic'][2]['RtTxBitrate']
                RT1_TX = MonitoringData['RequestData']['Traffic'][2]['RtTxBitrate']
                RT2_RX = MonitoringData['RequestData']['Traffic'][3]['RtTxBitrate']
                RT2_TX = MonitoringData['RequestData']['Traffic'][3]['RtTxBitrate']
                RT3_RX = MonitoringData['RequestData']['Traffic'][4]['RtTxBitrate']
                RT3_TX = MonitoringData['RequestData']['Traffic'][4]['RtTxBitrate']

                if beamData['RequestData']['InitialCarrier1']['Enabled']:
                    centerFreq = beamData['RequestData']['InitialCarrier1']['Freq']
                    SymbolRate = beamData['RequestData']['InitialCarrier1']['SymbolRate']

                else:
                    centerFreq = beamData['RequestData']['InitialCarrier2']['Freq']
                    SymbolRate = beamData['RequestData']['InitialCarrier2']['SymbolRate']
                element = [{
                    "time": now,
                    "modem name": modemName,
                    "modemType": modemType,
                    "macaddress": macaddress,
                    "HPS": HPS,
                    "beamName": beamName,
                    "satnetName": satnetName,
                    'VNO': VNO,
                    "ActiveBeamID": activeBeamID,
                    "CF": centerFreq,
                    "SymbolRate": SymbolRate,
                    "RXvoltage": RXvoltage,
                    "ElevationOffset": ElevationOffset,
                    "LowBand_LO": LowBand_LO,
                    "HighBand_LO": HighBand_LO,
                    "BUC_LO": BUC_LO,
                    'temperature': temperature,
                    'cpuUsage': cpuUsage,
                    'forwardModcod': forwardModcod,
                    'uptime': uptime,
                    'ESN0': ESN0,
                    'ReceivePower': ReceivePower,
                    'BE_RX': BE_RX,
                    'BE_TX': BE_TX,
                    'CD1_RX': CD1_RX,
                    'CD1_TX': CD1_TX,
                    'CD2_RX': CD2_RX,
                    'CD2_TX': CD2_TX,
                    'CD3_RX': CD3_RX,
                    'CD3_TX': CD3_TX,
                    'RT1_RX': RT1_RX,
                    'RT1_TX': RT1_TX,
                    'RT2_RX': RT2_RX,
                    'RT2_TX': RT2_TX,
                    'RT3_RX': RT3_RX,
                    'RT3_TX': RT3_TX
                }]
                self.writeToCSV(element)
            except Exception as e:
                print(e)
                pass

    '''
    # To make the script running more efficient, using gevent to run modeminfoList simutaneously. 100 terminals per modeminfoList
    '''

    def terminalGroup(self, modeminfoList, hubs):
        gevent.joinall([gevent.spawn(self.terminalParser, modem, hubs) for modem in modeminfoList])

    '''
    combine with gevent , use multiprocess pool will be more efficient, for my PC is 8 core, so I use 8.  one core for 100 terminals.
    '''

    def multi(self):
        a = mobilityParser(self.host, self.username, self.password)
        hubs = self.gethubmodule()
        count = a.getModemCount()
        res = a.getModem(count)
        pp = multiprocessing.Pool(8)
        for modeminfoList in res:
            pp.apply_async(self.terminalGroup(modeminfoList, hubs))
        pp.close()
        pp.join()

if __name__ == '__main__':
    host = '192.168.35.60'
    user = 'hno'
    password = 'D!@10g'
    a = mobilityParser(host, user, password)
    FILE = 'Mobilty Modem.csv'
    a.writeHeader()
    a.multi()
