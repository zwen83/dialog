# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/3/17
import requests
from rest import REST
import urllib.request
import json

ip = '192.168.48.42:14013'
username = 'hno'
password = 'D!@10g203'
rest = REST(ip, username=username, password=password)
terminal = rest.GET("modem?limit=200")
print(terminal)
print(len(terminal))
print(terminal[64]['remoteGuiUrl'])
#
index = 64
#
# # for index in len(terminal):
if 'tcs-2-0' in terminal[index]['remoteGuiUrl']:
    name = terminal[index]['id']['name']
    print(name)
    airMac = terminal[index]['macAddress']
    print(airMac)
    ipAddress = terminal[index]['networkSettingses'][0]['ipv4']['address']
    print(ipAddress)

    payload = {
        "bucSettings": {
            "bucAndModemFrequencySynchronized": True,
            "bucMaxFrequencyUncertainty": 1,
            "frequencyUncertainty": 0
        },
        "communicationsOnTheMove": {
            "enabled": False,
            "frequencyUncertainty": 0,
            "maximumSpeed": 0
        },
        "cpmSettings": None,
        "debugMode": False,
        "description": "",
        "encryptTraffic": None,
        "forwardClassificationProfileId": {
            "domainId": 1,
            "domainName": "System",
            "name": "best-effort-only",
            "systemId": 4
        },
        "forwardPoolId": {
            "domainId": 6,
            "domainName": "hno",
            "name": "FWD2",
            "systemId": 1300
        },
        "hrcMxDmaSettings": {
            "aupcEnabled": True,
            "aupcRange": 6,
            "hrcMxDmaReturnCapacityGroupId": {
                "domainId": 6,
                "domainName": "hno",
                "name": "IB_SLOT_SN42",
                "systemId": 3852
            },
            "modCod": "QPSK7/20",
            "modemId": {
                "domainId": 7,
                "domainName": "vno-1",
                "name": name,
                "systemId": 2616
            },
            "powerSettings": {
                "calculatedOutputPowerDbm": -15.127182,
                "outputPowerDbm": 1,
                "powerControlMode": "Nominal"
            },
            "returnPoolId": {
                "domainId": 6,
                "domainName": "hno",
                "name": "IB_SLOT_SN42",
                "systemId": 3855
            }
        },
        "hrcScpcSettings": None,
        "id": {
            "domainId": 7,
            "domainName": "vno-1",
            "name": "TEST_TEBET",
            "systemId": 2616
        },
        "lineUpSettings": {
            "nominalBandwidthHz": 1000000,
            "nominalOutputPowerDbm": -5,
            "outputPower1DbCompression": 5,
            "psd": -65
        },
        "locked": False,
        "macAddress": airMac,
        "managementAddress": "169.254.11.23",
        "monitoringType": "Advanced",
        "multicastCircuitIds": [],
        "networkSettingses": [
            {
                "type": "VIRTUAL",
                "description": None,
                "id": {
                    "domainId": 7,
                    "domainName": "vno-1",
                    "name": "4214",
                    "systemId": 4214
                },
                "ipv4": {
                    "address": ipAddress,
                    "dhcpMode": "Disabled",
                    "lanAddressPingable": True,
                    "prefixLength": 29,
                    "subnetRoutes": []
                },
                "ipv6": None,
                "networkId": {
                    "domainId": 6,
                    "domainName": "hno",
                    "name": "Test-network",
                    "systemId": 1268
                },
                "vlanTag": None
            }
        ],
        "remoteGuiUrl": "/remote-gui/hm-9/tcs-2-0/domain-7/terminal-2616/",
        "returnClassificationProfileId": {
            "domainId": 1,
            "domainName": "System",
            "name": "best-effort-only",
            "systemId": 4
        },
        "returnTechnology": "HRC_MXDMA",
        "routeAdvertisementSettings": {
            "loggedOn": False,
            "mode": "STATIC"
        },
        "s2Settings": None,
        "satelliteNetworkId": {
            "domainId": 6,
            "domainName": "hno",
            "name": "Satnet-42",
            "systemId": 1222
        },
        "serviceProfileId": {
            "domainId": 6,
            "domainName": "hno",
            "name": "Up_To_4Mbps",
            "systemId": 3373
        },
        "softwareUpdateGroup": 0,
        "tellinetInstanceId": {
            "domainId": 6,
            "domainName": "hno",
            "name": "1228",
            "systemId": 1228
        },
        "type": "MDM3100"
    }
# print(type(payload))
# jsonStr = json.dumps(payload)
# print(type(jsonStr))
# print(jsonStr)
# url = r'http://192.168.48.42:15013/rest/modem/'
# auth1 = ("hno", "D!@10g201")
# headers = {"Content-Type": "application/json",
#     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
# response = requests.post(url, data=jsonStr, auth=auth1, headers=headers, timeout=400)
# responseData=response.text
#
# print(responseData)

    ip1 = '192.168.48.42:15013'
    username1 = 'hno'
    password1 = 'D!@10g201'

    rest = REST(ip1,  username=username1, password=password1)
    print(payload)
    terminal = rest.POST("modem",payload=payload)




# if terminal and type(terminal) == dict and 'id' in terminal:
#     terminalId = terminal['id']['systemId']
#
# if 'tcs-2-0' in terminal['remoteGuiUrl']:
#     satnet = 1
#
# print('Rebooting terminal %s/%s in SatNet-%i with id=%i' % (domain, modem, satnet, terminalId))
# service = '/remote-gui/hm-9/CSE-%i-0/ftb-device-manager' % satnet
# rest.POST('lifecycle/terminal/%i/reboot' % terminalId, '', service)



