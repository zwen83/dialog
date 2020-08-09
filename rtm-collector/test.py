# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/4/28

import os,logging,datetime,platform,time
import argparse
import json
import math

def arg_parser():
    if 'windows' in platform.system().lower():
        default_log_path = 'c:/temp/rtm-collector.log'
    else:
        default_log_path = '/var/log/rtm-collector/rtm-collector.log'

    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', help = 'Polling interval. Default value: 10s', type = int, default = 10)
    parser.add_argument('--log', help = 'Location of the logfile. Default value: {0}'.format(default_log_path), type = str, default = default_log_path)
    parser.add_argument('--loglevel', help = 'Loglevel. Default value: INFO', type = str, default = 'INFO')
    parser.add_argument('--host', help = 'Destination host for the collected metrics. Default value: localhost', type = str, default = 'localhost')
    parser.add_argument('--port', help = 'Destination port for the collected metrics. Default value: 8186', type = int, default = 8186)
    parser.add_argument('--database', help = 'Database to store the collected metrics. Default value: telegraf', type = str, default = 'telegraf')
    parser.add_argument('--mode', help = 'How this script is run: DAEMON | RUNONCE. Default value: DAEMON', type = str, default = 'RUNONCE')
    parser.add_argument('--prov', help = 'Provosioning data location represented as a json key/value collection. Could be used to pass in provisioning related arguments. No default value', type = json.loads)
    parser.add_argument('--src-host', help = 'ip address of the source to be queried', type = str, default = '127.0.0.1')
    parser.add_argument('--src-port', help = 'port of the source to be queried', type = int, default = 10210)
    parser.add_argument('--fallible', help='flag to indicate if the collector is allowed to fail (used for testing)', type=bool, default = False)
    parser.add_argument('--config', help = 'location + filename of a yaml file containing all possible config', type = str, default = './test_config/base_config.yaml')
    args = parser.parse_args()
    return args


print(arg_parser())



class CollectorConfig(dict):
    def __getattr__(self, item):   # #调用类中原本没有定义的属性时候，调用__getattr__
        if item in self:
            return self[item]
        return None

    def __setattr__(self, item, value): ##对实例的属性进行赋值的时候调用__setattr__
        self[item] = value


collector_config = CollectorConfig(a=1, b=2)

d = dict(c=2,d=4)

print(d['c'])
# print(d.c)

print(collector_config['a'])


print(collector_config.a)

collector_config.a = 100

print(collector_config['a'])

def get_polling_time(interval):
    tm = time.time()
    return int(math.floor(tm / float(interval))) * int(interval)


print(time.time())
print(get_polling_time(30))


def file_has_changed(file, prev_modified_date, active_hps=None):
    if active_hps is not None:
        file = file.format(active_hps)
    try:
        modified_date = os.path.getmtime(unicode(file))
        return (modified_date > prev_modified_date, modified_date)
    except:
        logging.exception("'{0}' can not be found".format(file))
        return (False, 0)


print()
file = '/var/ntc-active-if/rtmc/rtn-terminals'

file = file.format(1)

print(file)


content = ['700|BE','763|BE','914|BE']
terminal_provisioning_data = []
terminal_provisioning_data = [x.strip().split('|') for x in content]


print(terminal_provisioning_data)
