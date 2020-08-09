# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/19

import datetime
import requests
from rest import REST

now = datetime.datetime.utcnow().isoformat().split("T")[0].replace("-","")

# rest = REST('10.255.0.63:35006', 'hno', 'D!@10g')
# json = rest.GET('tics/rest/event')

auth1 = ("hno", "D!@10g")
headers = {'Content-Type': '*/*',
           'Accept': 'application/json'}

url = 'http://10.255.0.63:35006/tics/rest/event'
res = requests.post(url=url, auth=auth1, headers=headers)
cookies = res.cookies
res1 = requests.get(url=url, auth=auth1, headers=headers, cookies=cookies)
data2 = res1.json()

print(data2)
print(type(data2))

