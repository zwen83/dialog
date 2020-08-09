# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/3/7
from rest import REST
import datetime
import random
import time
import os
import csv
from csv import reader
import argparse
import logging
logging.getLogger('requests').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
import requests
from influxdb import InfluxDBClient
from functools import reduce
import json


# get all the modem and hub module list
platform = 'AMI'
ip = '192.168.48.42:36006'
username = 'hno'
password = 'D!@10g'

from bs4 import BeautifulSoup as bs
url = requests.get('http://192.168.48.42:41006/remote-gui/HM-1/DCP-1/tc-shape-server/www/group_table.html?NODE_NAME=unicast_traffic')
auth1 = ("hno", "D!@10g")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
response = requests.get(url, auth=auth1, headers=headers, timeout=400)
html = response.text

str = '''用BeautifulSoup解析数据  python3 必须传入参数二'html.parser' 得到一个对象，接下来获取对象的相关属性'''
html = bs(html, 'html.parser')
# 读取title内容
print(html.title)
attrs = html.title.attrs
print(attrs)
print(attrs['class'][0])  # 显示class里面的内容

print(html.body)  # 显示body内容

print(html.p.attrs)
print(html.select("#seeyou")[0].string)
