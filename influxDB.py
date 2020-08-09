# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/2/29
import rest
from rest import REST
import datetime
import csv
import logging
logging.getLogger('requests').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
import requests
from influxdb import InfluxDBClient
from functools import reduce
import json
import threading

def getMxDMAiD():
    rest = REST(ip, username, password)
    MxDMA = rest.GET('hrc-mxdma-return-capacity-group')
    IDList = list()

    for i in range(5):
        try:
            if MxDMA[i]['id']['systemId']:
                IDList.append(MxDMA[i]['id']['systemId'])
        except IndexError as e:
            break
    return IDList

def getSCPCiD():
    rest = REST(ip, username, password)
    SCPC = rest.GET('hrc-scpc-return-capacity-group')
    IDList = list()
    for i in range(5):
        try:
            if SCPC[i]['id']['systemId']:
                IDList.append(SCPC[i]['id']['systemId'])
        except IndexError as e:
            break
    return IDList

def gethubmodule():
    try:
        rest = REST(ip, username, password)
        hubmodule = rest.GET('hub-module')
        hubmoduleName = hubmodule[0]['devicePools'][0]['hubModuleId']['name']
        satnetID = hubmodule[0]['devicePools'][0]['hpsId']
        hubModuleType = hubmodule[0]['hubModuleType']
        return hubmoduleName
    except IndexError or TypeError as e:
        rest = REST(ip, username, password)
        hubmodule = rest.GET('hub-module')
        hubmoduleName = hubmodule[0]['hubModules'][0]['devicePools'][0]['hubModuleId']['name']
        return hubmoduleName

def gethubmoduleType():
    rest = REST(ip, username, password)
    hubmodule = rest.GET('hub-module')
    hubModuleType = hubmodule[0]['hubModuleType']
    return hubModuleType

def getSatnetCount(ip,username, password):
    rest = REST(ip, username, password)
    satnetNumber = rest.GET("satellite-network/count")
    return satnetNumber

def getSatnetName(ip,username, password):
    rest = REST(ip, username, password)
    satnetName = rest.GET("satellite-network")
    return satnetName

# poll the CSV data from metric collector export to a performanceDict
def GetPerformanceUrls(iCount=1, now=datetime.datetime.utcnow()):
    hubmoduleName = gethubmodule()
    filenames = list()
    now = now - datetime.timedelta(seconds=600)
    # for i in range(iCount):
    filenames.append('performance_%s%02i.csv' % (now.strftime('%Y%m%d%H'), now.minute - now.minute % 5))
    # now = now - datetime.timedelta(seconds=600)
    filenames.reverse()
    urls = list()
    url = '/remote-gui/%s/HMGW-0-0/mc/performance/' % hubmoduleName
    for filename in filenames:
        urls.append(url + filename)
    return "http://" + ip + urls[0]

def GetHRCControllerUrls(satnetID):
    hubmoduleName = gethubmodule()
    urls = list()
    urls.append('/remote-gui/%s/HMGW-0-0/hrccontroller-%s/statistics' % (hubmoduleName, satnetID))
    return "http://" + ip + urls[0]

def mySum (x,y):
    return x + y

def getSatnetCount(ip,username,password):
    rest = REST(ip, username, password)
    SatnetCount = rest.GET('satellite-network/count')
    return SatnetCount['count']

def getHRClogon(satnetNum):
    url = GetHRCControllerUrls(satnetNum)
    print(url)
    auth1 = ("hno", "D!@10g")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
    response = requests.get(url, auth=auth1, headers=headers, timeout=400)
    performance = json.loads(response.text)
    McDMARCG = getMxDMAiD()
    SCPCRCG = getSCPCiD()
    index = 0
    index1 = 0
    listDMA = list()
    listSCPC = list()
    for index in range(len(McDMARCG)):
        try:
            # int(performance['carrierGroups']['hrc_mxdma_rcg_'+str(i)]['loggedOnTerminals'])
            listDMA.append(int(performance['carrierGroups']['hrc_mxdma_rcg_'+str(McDMARCG[index])]['loggedOnTerminals']))
            McDMARCG.remove(McDMARCG[index])
            index += 1
        except KeyError as e:
            index += 1
        except IndexError as e:
            break

    try:
        sumHRCDMA = reduce(mySum, listDMA)
    except TypeError as e:
        sumHRCDMA = 0

    for index1 in range(len(SCPCRCG)+1):
        try:
            listSCPC.append(int(performance['carrierGroups']['hrc_scpc_rcg_' + str(SCPCRCG[index1])]['loggedOnTerminals']))
            SCPCRCG.remove(SCPCRCG[index1])
            index1 += 1
        except KeyError as e:
            index1 += 1
        except IndexError as e:
            break
    try:
        sumHRCSCPC = reduce(mySum, listSCPC)
    except TypeError as e:
        sumHRCSCPC = 0

    return sumHRCDMA + sumHRCSCPC

def getTerminalDict():
    hubmoduleName = gethubmodule()
    url = GetPerformanceUrls(hubmoduleName)
    print(url)
    auth1 = ("hno", "D!@10g")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
    response = requests.get(url, auth=auth1, headers=headers, timeout=400)
    performance = response.text.splitlines()

    performanceDict = csv.DictReader(response.text.splitlines())
    return performanceDict

def addPointRTN(pointList, measurement, value,platform, modemId,satnetID, now):
    fields = {'value': value}
    pointList.append({'fields': fields,'measurement': measurement,'tags': {'platform':platform,'modem_id': modemId,'satnet' : satnetID}, 'time': now})
    return pointList

def addPointFWD(pointList, measurement, value,platform,modemId,satnetID, now):
    fields = {'value': value}
    pointList.append({'fields': fields,'measurement': measurement,'tags': {'platform':platform,'modem_id': modemId,'satnet' : satnetID}, 'time': now})
    return pointList

def addPointlogon(pointList, logonTerminalNumber,platform, value,satnetID, now):
    fields = {'value': value}
    pointList.append({'fields': fields,'measurement': logonTerminalNumber,'tags': {'platform':platform,'satnet' : satnetID}, 'time': now})
    return pointList

def addPointTotalFWD(pointList, measurement,platform, value, satnetID, now):
    fields = {'value': value}
    pointList.append({'fields': fields,'measurement': measurement,'tags': {'platform':platform,'satnet' : satnetID}, 'time': now})
    return pointList

def addPointTotalRTN(pointList, measurement,platform, value, satnetID, now):
    fields = {'value': value}
    pointList.append({'fields': fields,'measurement': measurement,'tags': {'platform':platform,'satnet' : satnetID}, 'time': now})
    return pointList

def char2int(char):
    return {"0" : 0, "1" : 1, "2" : 2, "3" : 3, "4" : 4, "5" : 5, "6" : 6, "7" : 7, "8" : 7, "9" : 9 } [char]

def writeIntoInflux(ip,username,password,platform):
    hubmoduleName = gethubmodule()
    performanceDict = getTerminalDict()
    date = GetPerformanceUrls(hubmoduleName).split('_')[-1].split('.')[0]
    now = date[0:4] + '-' + date[4:6] + '-' + date[6:8] + ' ' + date[8:10] + ':' + date[10:12] + ':00'
    serverIP = "192.168.48.42"
    client = InfluxDBClient(serverIP, 8086, "root", "root", timeout=100)
    client.create_database('test')
    client.switch_database('test')
    for satnetNum in range(int(getSatnetCount(ip,username,password))):
        pointListHRC = list()
        try:
            satnetnumber = satnetNum+1
            HRCTotal = getHRClogon(satnetnumber)
            pointListLogon = addPointlogon(pointListHRC, "HRC Total logon Terminal",platform,HRCTotal, satnetnumber, now)
            client.write_points(pointListLogon)
        except json.decoder.JSONDecodeError as e:
            satnetNum += 1

def writesatnetInflux(ip, username, password,satnetNum,platform):
    hubmoduleName = gethubmodule()
    performanceDict = getTerminalDict()
    date = GetPerformanceUrls(hubmoduleName).split('_')[-1].split('.')[0]
    now = date[0:4] + '-' + date[4:6] + '-' + date[6:8] + ' ' + date[8:10] + ':' + date[10:12] + ':00'
    satnetName = getSatnetName(ip, username, password)
    print(satnetName)
    serverIP = "192.168.48.42"
    client = InfluxDBClient(serverIP, 8086, "root", "root", timeout=100)
    client.switch_database('test')
    index = 0
    satnetForwardTotal = []
    satnetReturnTotal = []
    for row in performanceDict:
        print(row)

        modemId = int(row['Modem id'])
        rest = REST(ip, username, password)
        modems = rest.GET('modem' + "/" + str(modemId) , timeout= 6000)
        try:
            satnetID = modems['satelliteNetworkConfigurations'][0]['satelliteNetworkId']['name']
        except TypeError as e:
            satnetID = modems['attachment']['satelliteNetworkId']['name']
        satnetNum1 = satnetNum + 1

        if satnetID == satnetName[satnetNum]['id']['name']:
            valueForwardTotalList1 = list()
            if row['Forward throughput BE']:
                valueForwardTotalList1.append(int(row['Forward throughput BE']))
            if row['Forward throughput CD1']:
                valueForwardTotalList1.append(int(row['Forward throughput CD1']))
            if row['Forward throughput CD2']:
                valueForwardTotalList1.append(int(row['Forward throughput CD2']))
            if row['Forward throughput CD3']:
                valueForwardTotalList1.append(int(row['Forward throughput CD3']))
            if row['Forward throughput RT1']:
                valueForwardTotalList1.append(int(row['Forward throughput RT1']))
            if row['Forward throughput RT2']:
                valueForwardTotalList1.append(int(row['Forward throughput RT2']))
            if row['Forward throughput RT3']:
                valueForwardTotalList1.append(int(row['Forward throughput RT3']))

            if valueForwardTotalList1:
                try:
                    valueForwardTotal = reduce(mySum, valueForwardTotalList1)
                    pointListF = list()
                    pointListFWD = addPointRTN(pointListF, "Forward Total", valueForwardTotal, platform, modemId,satnetID,now)
                    client.write_points(pointListFWD)
                except TypeError as e:
                    valueForwardTotal = 0
                    pointListF = list()
                    pointListFWD = addPointRTN(pointListF, "Forward Total", valueForwardTotal, platform, modemId,satnetID,now)
                    client.write_points(pointListFWD)
            try:

                valueForwardTotal1 = reduce(mySum, valueForwardTotalList1)
                satnetForwardTotal.append(valueForwardTotal1)
            except TypeError as e:
                satnetForwardTotal.append(0)

            valueReturnTotalList1 = list()
            if row['Return throughput BE']:
                valueReturnTotalList1.append(int(row['Return throughput BE']))
            if row['Return throughput CD1']:
                valueReturnTotalList1.append(int(row['Return throughput CD1']))
            if row['Return throughput CD2']:
                valueReturnTotalList1.append(int(row['Return throughput CD2']))
            if row['Return throughput CD3']:
                valueReturnTotalList1.append(int(row['Return throughput CD3']))
            if row['Return throughput RT1']:
                valueReturnTotalList1.append(int(row['Return throughput RT1']))
            if row['Return throughput RT2']:
                valueReturnTotalList1.append(int(row['Return throughput RT2']))
            if row['Return throughput RT3']:
                valueReturnTotalList1.append(int(row['Return throughput RT3']))

            if valueReturnTotalList1:
                try:
                    valueReturnTotal = reduce(mySum, valueReturnTotalList1)
                    pointListR = list()
                    pointListRTN = addPointRTN(pointListR, "Return Total", valueReturnTotal, platform, modemId,satnetID,now)
                    client.write_points(pointListRTN)
                except TypeError as e:
                    valueReturnTotal = 0
                    pointListR = list()
                    pointListRTN = addPointRTN(pointListR, "Return Total", valueReturnTotal, platform, modemId,satnetID,now)
                    client.write_points(pointListRTN)

                try:
                    valueReturnTotal1 =  reduce(mySum,valueReturnTotalList1)
                    satnetReturnTotal.append(valueReturnTotal1)
                except TypeError as e:
                    satnetReturnTotal.append(0)
    return satnetForwardTotal,satnetReturnTotal


def MainRun(ip, username, password,platform):
    platformList = {'AMI': '192.168.48.126:36006',
                    'BCnet': '192.168.48.125:35006',
                    'Bambu': '192.168.48.131:41006',
                    'infokom1': '192.168.48.128:38006',
                    'infokom2': '192.168.48.129:39006',
                    'patrakom': '10.255.0.99:24006',
                    'PSN2': '192.168.48.132:42006',
                    'skyreach': '192.168.48.134:44006',
                    'Telered': '192.168.48.130:40006',
                    'TNIC': '192.168.48.136:46006',
                    'TNIK': '192.168.48.137:47006',
                    'Stella': '10.255.0.100:25006'}
    username = 'hno'
    password = 'D!@10g'
    global ip
    global platform
    try:
        for platform, ip in platformList.items():
            writeIntoInflux(ip, username, password,platform)
            for satnetNum in range(int(getSatnetCount(ip,username,password))):
                satnetName = getSatnetName(ip, username, password)
                satnetID = satnetName[satnetNum]['id']['name']
                hubmoduleName = gethubmodule()
                performanceDict = getTerminalDict()
                date = GetPerformanceUrls(hubmoduleName).split('_')[-1].split('.')[0]
                now = date[0:4] + '-' + date[4:6] + '-' + date[6:8] + ' ' + date[8:10] + ':' + date[10:12] + ':00'
                serverIP = "192.168.48.42"
                client = InfluxDBClient(serverIP, 8086, "root", "root", timeout=100)
                client.switch_database('test')
                try:
                    res = writesatnetInflux(ip, username, password,satnetNum,platform)
                    pointListTR = []
                    pointListTF = []
                    valueSatnetForwardTotal = reduce(mySum, res[0])
                    pointListSatnetFWD = addPointTotalFWD(pointListTF, "Forward Satnet Total", platform,
                                                          valueSatnetForwardTotal, satnetID, now)
                    client.write_points(pointListSatnetFWD)
                    valueSatnetReturnTotal = reduce(mySum, res[1])
                    pointListSatnetRTN = addPointTotalRTN(pointListTR, "Return Satnet Total", platform,
                                                          valueSatnetReturnTotal, satnetID, now)
                    client.write_points(pointListSatnetRTN)
                except IndexError as e:
                    pass
                except TypeError as e:
                    pass
                except rest.DialogError as e:
                    pass
    except rest.ConnectionError as e:
        pass
    timer = threading.Timer(3000,MainRun,[ip, username, password,platform])
    timer.start()
    timer.join()



if __name__ == "__main__":
    username = "hno"
    password = "D!@10g"

    try:
        t= threading.Thread(target=MainRun)
        t.start()
        t.join()
    except rest.ConnectionError as e:
        pass
    except rest.DialogError as e:
        pass







