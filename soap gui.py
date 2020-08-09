# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/2/26



ip = '192.168.48.230'  #change to your ip
username ='hno' # your username
password ='D!@10g'   # its password

import ssl
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

from suds.client import Client
url = 'http://%s/API/V1/soap.asmx?wsdl' % ip
interface = Client(url, username=username, password=password)
connection = interface.service.ConnectApp('localhost', username, password, 'test', '?', '?')
print("A connection is established: " + connection)

DMAID='28770'  #change the IDs appropriately
ElementID='40'
ParameterID='1091'

c=interface.service.GetParameter(connection, DMAID, ElementID, ParameterID)
print(c.DisplayValue)
