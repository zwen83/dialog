# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/7/10

import json, urllib, base64,requests

ip = 'http://10.25.10.180:8086'

query1 = 'select * from "forward.shaper" where time > now()-2m limit 2'
# query = 'SELECT LAST(\"' + field + '\") FROM \"' + series + '\" WHERE \"' + key + '\"=\'' + keyvalue + '\''
# print query
collectmethod = '/query?db=telegraf&q=' + query1
url = ip + collectmethod
auth1 = ('hno', '=kQ9+bQ(B+kh2NbD')
headers1 = {'Content-Type': '*/*',
            'Accept': 'text/html'}
res = requests.post(url=url, auth=auth1, headers=headers1)
cookies = res.cookies
result = requests.get(url, headers=headers1, cookies=cookies)
print(result)
resData = result.json()
print(resData)
