# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/20

import requests
from rest import REST
import urllib.request
import json

ip = '192.168.48.129:39006'
username = 'hno'
password = 'D!@10g'
rest = REST(ip, username=username, password=password)
terminal = rest.GET("modem?limit=300")
print(terminal)
print(len(terminal))


for i in range(len(terminal)):
    terminal[i]['skipCertification'] = 'True'
    print(terminal[i])
    print(type(terminal[i]))

    # path2 = r"C:\Users\zwen.073111-PC\爬虫\qq\{}.json".format(terminal[i]['id']['systemId'])
    # with open(path2, "w") as f:
    #     json.dump(terminal[i], f)
    terminalID = terminal[i]['id']['systemId']
    url = "modem/{}".format(terminalID)
    print(url)
    print(type(url))

    rest.PUT(url, terminal[i])
    # rest.DELETE(url)

    # with open(path2, "r") as f:
    #     data1=json.loads(f)
    #     print(data1)


# #
#
#
#
#
#     jsonStr = json.dumps(payload)
#     ip1 = '192.168.48.42:15013'
#     username1 = 'hno'
#     password1 = 'D!@10g201'
#     rest = REST(ip1,  username=username1, password=password1)
#     print(payload)
#     terminal = rest.POST("modem",payload=payload)


# if terminal and type(terminal) == dict and 'id' in terminal:
#     terminalId = terminal['id']['systemId']
#
# if 'tcs-2-0' in terminal['remoteGuiUrl']:
#     satnet = 1
#
# print('Rebooting terminal %s/%s in SatNet-%i with id=%i' % (domain, modem, satnet, terminalId))
# service = '/remote-gui/hm-9/CSE-%i-0/ftb-device-manager' % satnet
# rest.POST('lifecycle/terminal/%i/reboot' % terminalId, '', service)
