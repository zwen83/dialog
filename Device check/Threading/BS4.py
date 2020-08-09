# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/27

from bs4 import BeautifulSoup
import requests
import re

url = r"http://10.255.0.63/remote-gui/KAC_SUB-1_ENCL-1/DCP-2/tc-shape-server/www/group_table.html"
auth1 = ("hno", "D!@10g")
headers = {'Content-Type': '*/*',
           'Accept': 'text/html'}
res = requests.post(url=url, auth=auth1, headers=headers)
cookies = res.cookies
res1 = requests.get(url=url,auth=auth1,headers=headers,cookies=cookies)

# print(res1.text)

soup = BeautifulSoup(res1.text,'lxml')

data1 = soup.font.contents[-1]

data2 = str(data1)
print(data2)
print(type(data2))

# for i,value in enumerate(data1):
#     print("{}----{}".format(i,value))

patdcp = r'"right">(.*?) bits/s</td>'
dataDCPrate = re.compile(patdcp)
data = dataDCPrate.findall(data2)
print(data)

for i , rate in enumerate(data):
    print("{}----{}".format(i,rate))

# dcpDroprate = dataDCPrate.findall(dcpdroprate)

dcptotalrate = data[4].split(",")
dcpdroprate = data[2].split(",")
# print(dcptotalrate)


total = ''
for i in dcptotalrate:
    total += i
dcpTotalRate = int(total)

total1 = ''
for i in dcpdroprate:
    total1 += i
dcpDropRate = int(total1)

print(dcpTotalRate)
print(dcpDropRate)



# for i , rate in enumerate(data):
#     print("{}----{}".format(i,rate))
# table = soup.font.contents
# print(table[-1])
# soup1 = BeautifulSoup(table[-1],'lxml')
# lines = soup1.table.descendants
# for i,data in enumerate(lines):
#     print("{}----{}".format(i,data))





