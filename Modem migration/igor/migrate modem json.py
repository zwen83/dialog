# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/20


# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/16


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
import requests
from rest import REST
import json
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

try:
    import configparser
except ImportError:
    print('This script uses "configparser" as an external module. Please install it prior to usage.')
    print('You can install it as a root user: "pip3 install configparser" or "pip install configparser"')
    exit(1)

# http://10.255.0.91:16006/remote-gui/NRD_X01_ENCL-1/tcs-1-0/domain-15/terminal-18037/cgi-bin/index
class mobilityParser(object):
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.HPS1 = [1, 2, 3, 4, 5, 6]
        self.HPS2 = [8, 9, 10, 11, 12, 13]
        self.HPS3 = [15, 16, 17, 18, 19, 20]

    def ReadConfig(self):
        configuration = configparser.ConfigParser()
        configuration.optionxform = lambda option: option

        iniFileName = 'change_sat_config.ini'
        res = configuration.read(iniFileName)
        # print(res)
        # print(len(configuration))
        if len(configuration) < 2:
            print('%s file not found' % iniFileName)
            exit(1)
        # check for obligitary settings in the .ini file
        config = dict()
        for section in configuration:
            config[section] = dict()
            # print(configuration[section])  # <Section: Other>
            for key in configuration[section]:
                config[section][key] = configuration[section][key]  # 将configuration读出来的配置写入config里
                # print(config)
        for key in ['Access', 'Satnet']:
            if key not in config:
                print('No %s section found in the .ini file' % key)
                exit(1)
        return config
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
        config = self.ReadConfig()
        hubName = config['Satnet']['hubName']
        ENCLnum = config['Satnet']['ENCLnum']

        # hubencl = hubName + '_ENCL-' + ENCLnum
        hubencl = 'HM-1'
        HPS = config['Satnet']['HPS']

        for i in range(count + 1):
            start = (i * 100)
            if i == (count + 1):
                modem = rest.GET('modem?limit={}&start={}'.format((count1 - 1), start))
                for x in modem:
                    url = x['remoteGuiUrl']
                    if hubencl == re.split('/', url)[2] and HPS == re.split('-', url)[3]:
                        urlList.append((x['remoteGuiUrl'],x['macAddress'], x['id']['domainName'], x['id']['name'], x['locked']))
            else:
                modem = rest.GET('modem?limit=100&start={}'.format(start))
                for y in modem:

                    url = y['remoteGuiUrl']
                    url1 = re.split('/', url)[2]
                    url2 = re.split('-', url)[3]
                    if hubencl == url1 and HPS == url2:
                        urlList.append((y['remoteGuiUrl'], y['macAddress'], y['id']['domainName'], y['id']['name'], y['locked']))
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
            print(func)
            auth1 = (self.username, self.password)
            headers = {'TextId': 'request'}
            result = requests.post(url, data=func, headers=headers,auth=auth1)
            print(result.status_code)
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
        func = {'request': '{"SessionId": "' + sessionID + '", "FunctionName":"AddBeam","Params": { "InitialCarrier1" : { "Freq" : 12500000000, "SymbolRate" : 10000000, "TSMode" : "dvbs2x", "Polarization"     : 0, "Enabled" : true }, "PointingCarrier1" : { "Carrier" : { "Freq" : 12500000000, "SymbolRate" : 10000000, "TSMode" : "dvbs2x", "Polarization" : 0, "Enabled" : true } }, "InitialCarrier2" : { "TimeSliceNumber" : 1, "Freq" : 0, "SymbolRate" : 0, "TSMode" : "dvbs2x", "Polarization" : 0, "Enabled" : false }, "PointingCarrier2" : { "Carrier" : { "TimeSliceNumber" : 1, "Freq" : 0, "SymbolRate" : 0, "TSMode" : "dvbs2x", "Polarization" : 0, "Enabled" : false } }, "PolarizationSkew" : 0, "OrbitalDegrees" : 0, "SatLatitudeVariance" : 0, "MaxSkew" : 0, "DefaultInitialCarrier" : 1, "DefaultPointingCarrier" : 1, "Hemisphere" : "east", "TxPolarization" : 0, "AcuXString" : "", "BeamName" : "", "Cost" : 0, "AutomaticPointingTimeout" : 210000, "GxtFileName" : "", "ExclusionZones" : [  ], "BeamId" : 18 }}'}
        method = "POST"
        return self.sendRequest(url, func, method)

    def createBeam2(self,activebeamID,beamData,freq,SymbolRate,TSMode,Polarization):
        beamData1 = beamData['RequestData']
        Enabled = True
        InitialCarrier2 = {"TimeSliceNumber": 1, "Freq": freq, "SymbolRate": SymbolRate, "TSMode": TSMode, "Polarization": Polarization, "Enabled": Enabled}
        point2 = {"TimeSliceNumber": 1, "Freq": freq, "SymbolRate": SymbolRate, "TSMode": TSMode, "Polarization": Polarization,"Enabled": Enabled}
        PointingCarrier2 = {"Carrier": point2}
        beamData1["InitialCarrier2"] = InitialCarrier2
        beamData1["PointingCarrier2"] = PointingCarrier2
        beamData1["BeamId" ] = activebeamID
        return beamData1

    def createBeam1(self,activebeamID,beamData,freq,SymbolRate,TSMode,Polarization):
        beamData1 = beamData['RequestData']
        Enabled = True
        InitialCarrier1 = {"TimeSliceNumber": 1, "Freq": freq, "SymbolRate": SymbolRate, "TSMode": TSMode, "Polarization": Polarization, "Enabled": Enabled}
        point1 = {"TimeSliceNumber": 1, "Freq": freq, "SymbolRate": SymbolRate, "TSMode": TSMode, "Polarization": Polarization,"Enabled": Enabled}
        PointingCarrier1 = {"Carrier": point1}
        beamData1["InitialCarrier1"] = InitialCarrier1
        beamData1["PointingCarrier1"] = PointingCarrier1
        beamData1["BeamId" ] = activebeamID
        return beamData1


    def setBeam(self,url,beam):
        funcname = '"Params": %s' % beam
        sessionID = self.authenticate(url)
        func = {'request': '{"SessionId": "' + sessionID + '", "FunctionName":"SetBeamData",%s }' % funcname}
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
                  'cpuUsage', 'forwardModcod', 'uptime', 'ESN0', 'ReceivePower']
        with open(FILE, 'a', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, header)
            dict_writer.writerows(modemList)

    def writeHeader(self):
        FILE = 'Mobilty Modem.csv'
        logger.info('Write CSV header to {}'.format(FILE))
        header = ['time', 'modem name', 'modemType', 'macaddress', 'HPS', 'beamName', 'satnetName', 'VNO',
                  'ActiveBeamID', 'CF',
                  'SymbolRate', 'RXvoltage', 'ElevationOffset', 'LowBand_LO', 'HighBand_LO', 'BUC_LO', 'temperature',
                  'cpuUsage', 'forwardModcod', 'uptime', 'ESN0', 'ReceivePower']
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
        config = self.ReadConfig()
        freq = int(config['Satnet']['alternativeFrequency'])
        SymbRate = int(config['Satnet']['alternativeSymbolRate'])
        TSMode = config['Satnet']['TSMode']
        Polarization = int(config['Satnet']['Polarization'])
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
            for hub in hubs:
                if hub['hubProcessingSegmentId']['name'].split(".")[-1].split("-")[-1] == HPS:  #need to add one more critria
                    beamName = hub['beamId']['name']
                    satnetName = hub['id']['name']

            # try:
            # self.addBeam(urlFinal)
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
            if beamData['RequestData']['DefaultInitialCarrier']==1:
                centerFreq = beamData['RequestData']['InitialCarrier1']['Freq']
                SymbolRate = beamData['RequestData']['InitialCarrier1']['SymbolRate']
                newBeamData = self.createBeam2(activeBeamID, beamData, freq, SymbRate, TSMode, Polarization)
                newBeamDatastr = json.dumps(newBeamData)
                self.setBeam(urlFinal, newBeamDatastr)
            else:
                centerFreq = beamData['RequestData']['InitialCarrier2']['Freq']
                SymbolRate = beamData['RequestData']['InitialCarrier2']['SymbolRate']
                newBeamData1 = self.createBeam1(activeBeamID, beamData, freq, SymbRate, TSMode, Polarization)
                newBeamDatastr1 = json.dumps(newBeamData1)
                self.setBeam(urlFinal, newBeamDatastr1)
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
            }]
            self.writeToCSV(element)
            # except Exception as e:
            #     print(e)
            #     pass



    def terminalGroup(self, modeminfoList, hubs):
        gevent.joinall([gevent.spawn(self.terminalParser, modeminfoList, hubs )])

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
            pp.apply_async(self.terminalParser(modeminfoList, hubs))
        pp.close()
        pp.join()

if __name__ == '__main__':
    host = '10.60.205.10'
    user = 'hno'
    password = 'D!@10g'
    a = mobilityParser(host, user, password)
    FILE = 'Mobilty Modem.csv'
    a.writeHeader()
    a.multi()
