# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/4/1
import influxdb
from influxdb import InfluxDBClient
import json

class influxWriter(object):
    def __init__(self,ip, username, password,database,points):
        self.ip = ip
        self.username = username
        self.password = password
        self.database =database
        self.points = points
    def writer(self):
        client = InfluxDBClient(self.ip, 8086, self.username, self.password, timeout=100)
        client.create_database(self.database)
        client.switch_database(self.database)
        client.write_points([self.points])


