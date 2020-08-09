# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/9
import json
import logging
import requests
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',datefmt='%a, %d %b %Y %H:%M:%S',filename='readDate.log',filemode='w')
from restTICS import REST
import csv
# with open('test.csv', 'w', newline='') as csvfile:
#     fieldnames = ['first_name', 'last_name']
#     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#
#     writer.writeheader()
#     writer.writerow({'first_name': 'Baked', 'last_name': 'Beans'})
#     writer.writerow({'first_name': 'Lovely', 'last_name': 'Spam'})
#     writer.writerow({'first_name': 'Wonderful', 'last_name': 'Spam'})
ip = '192.168.48.129:39006'
url = 'http://{}/tics/rest/terminal'.format(ip)
with open('test.csv', 'r') as csvfile:
    #fieldnames = ['first_name', 'last_name']
    reader = csv.DictReader(csvfile)
    for row in reader:
        print(row['macAddress'],row['name'],row['latitude'],row['longitude'])
jsonData = {
				"macAddress": "00:06:39:8a:af:7a",
				"name": "Test_Demo-2",
				"ipAddress": None,
				"networks": None,
				"latitude": -6,
				"longitude": 116,
				"nominalEsN0": None,
				"currentEsN0": None,
				"targetEsN0": None,
				"satelliteNetwork": {
				"id": 3,
				"dialogId": None
				},
				"domain": {"id": 195
				},
				"nominalBandwith": None,
				"nominalOutputPower": None,
				"referenceTerminal": None,
				"password": None,
				"failedCertificationCount": None,
				"dialogId": 3204,
				"certifiedTimestamp": None,
				"deletedTimestamp": None,
				"beam": None,
				"remoteUrl": "/remote-gui/LIQ-KRU-1/tcs-3-0/domain-1105/terminal-3204/",
				"nominalCN0": None,
				"currentCN0": None,
				"targetCN0": None,
				"pModem1db": None,
				"certificationMeasurementStatus": None,
				"certificationAdministrativeStatus": 'CERTIFIED'
			}
print(type(jsonData))
# jsonData = json.dumps(jsonData)
# print(jsonData)
# print(type(jsonData))
rest = REST(ip, 'hno', 'D!@10g')
rest.POST('terminal',payload=jsonData)
terminals = rest.GET('terminal')
print(terminals)

# auth1 = ("hno", "D!@10g")
# headers = {'Content-Type': '*/*',
# 		   'Accept': 'text/html'}
# res = requests.post(url=url, auth=auth1, headers=headers,json=jsonData)
# cookies = res.cookies
# res1 = requests.get(url=url, auth=auth1, headers=headers, cookies=cookies)
# print(res1)