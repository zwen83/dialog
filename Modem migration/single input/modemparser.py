# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/7/2
from rest import REST
import gevent
from gevent import monkey
from DialogAPI import DialogAPI
monkey.patch_all(thread=False)
import logging
import re
import datetime

import csvhandler


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

def modemParser(modemList, hubs,host,username,password):
    Dialogapi = DialogAPI(host,username,password)
    now = datetime.datetime.utcnow().isoformat().split(".")[0]
    if not modemList[-1]:
        macaddress = modemList[1]
        url = modemList[0]
        urlFinal = 'http://' + host + url + 'cgi-bin/cgiclient?request='
        logger.info("trying to reach to modem remote gui=>{}".format(urlFinal))
        VNO = modemList[2]
        modemName = modemList[3]
        logger.info("get modem - {} parameter".format(modemName))
        HPS = re.split('-', url)[4]
        a = re.split('/', url)[2].split("_")
        hubmodule = a[0] + '_' + a[1]
        for hub in hubs:
            if (hub['hubProcessingSegmentId']['name'].split(".")[-1].split("-")[-1] == HPS and
                hub['hubProcessingSegmentId']['name'].split(".")[0]) == hubmodule:
                beamName = hub['beamId']['name']
                satnetName = hub['id']['name']
        try:
            # Dialogapi.addBeam(urlFinal)
            activeBeamID = Dialogapi.getActiveBeam(urlFinal)
            beamData = Dialogapi.getBeamData(activeBeamID, urlFinal)
            MonitoringData = Dialogapi.getMonitoringData(urlFinal)
            print(MonitoringData)
            print(type(MonitoringData))
            modemType = MonitoringData['RequestData']['System']['Desc']
            temperature = MonitoringData['RequestData']['Status']['Temp']
            cpuUsage = MonitoringData['RequestData']['Status']['CpuUsage'][0]
            forwardModcod = MonitoringData['RequestData']['Demods'][0]['Modcod']
            uptime = MonitoringData['RequestData']['System']['UpTime']
            ESN0 = MonitoringData['RequestData']['Demods'][0]['EsN0']
            ReceivePower = MonitoringData['RequestData']['Demods'][0]['RxPwr']
            ActiveODUType = Dialogapi.getActiveODUType(urlFinal)
            ODUTypeData = Dialogapi.getODUTypeData(urlFinal, ActiveODUType)
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
                "hub module": hubmodule,
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

                'BE_RX' : BE_RX,
                'BE_TX': BE_TX,
                'CD1_RX' : CD1_RX,
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
            print(element)
            csvhandler.writeToCSV(element)

        except Exception as e:
            print(e)
            pass