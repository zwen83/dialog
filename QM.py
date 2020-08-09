# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/22

#!/usr/bin/python3
import json
import requests
import datetime
import pyinputplus
import logging

__author__ = "Ramkumar Balaguru, rbal@idirect.net"

logger=logging.Logger("logger1")
logger.setLevel(logging.DEBUG)
handler1=logging.FileHandler("vno_volume_mail.log",mode="a")
handler1.setLevel(logging.DEBUG)
logger.addHandler(handler1)



headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic aG5vOkQhQDEwZw==',
}


headers={'Content-Type': 'application/vnd.newtec.conf-v1+json', 'Accept': 'application/json'}
x_h=pyinputplus.inputPassword(prompt="Enter the credentials for hno user: ",mask="*")
auth1=("hno",x_h)

# From and To date for which you need the data date. Uses the ISO8601 format (yyyy-MM-ddTHH:mm:ss.SSSZ)


t1 = (datetime.datetime.now(datetime.timezone.utc) -
         datetime.timedelta(minutes=390)).strftime("%Y-%m-%dT%H:%M")
t2 = (datetime.datetime.now(datetime.timezone.utc) -
         datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M")

# '2020-05-21T21:10' - If you want to manually define the dates kindly use this format and directly assign values as show below
# Take note the time is in gmt
# t1 = '2020-05-21T21:10'
# t2= '2020-05-21T23:10'

params = (
    ('from', t1),
    ('to', t2),
)

#print(params)


#Generate list of vnos
url1="http://10.0.10.27/qm/rest/vnos"
try:
	rsp = requests.get(url=url1, headers=headers, auth=auth1,params=params)
	data=rsp.text
	#print(rsp.content)
	data=json.loads(data)
except:
	logger.error(f"There is an error in accesing the QM")

list1=[]
for index,val in enumerate(data):
	x=str(val["id"])
	list1.append(x)
	# print(list1)

for _ in list1:
	url="http://10.0.10.27/qm/rest/accounting/json/"+_
	try:
		rsp = requests.get(url=url, headers=headers, auth=auth1,params=params)
		data=rsp.text
	#print(rsp.content)
		data=json.loads(data)["csv"]
	except:
		logger.error(f"There is an error in accesing the QM")

	if (rsp.status_code == 200):
		logger.info(rsp.status_code)
		logger.info("Data is accessible and we will proceed")
		#print(data["csv"])
		with open(r"C:\scripts\volume.csv", mode="a+") as fs:
			fs.write(data)