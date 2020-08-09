# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/8/5

import re


url = '/remote-gui/ECOXIF_ENCL-1/tcs-2-0/domain-133/terminal-931/'

res = re.split('/', url)[2]

print(res)

res1 = re.split('-', url)[3]

print(res1)