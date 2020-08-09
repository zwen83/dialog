# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/7/20
import time
import subprocess
import os
OOOLO = os.popen('cd /usr/local/amp/amp1/&&cat $(ls -t ./output/sit* | head -1) | grep OUT | wc -l').read()

debasd = os.popen('''cd /usr/local/amp/amp1/output/&&/usr/local/amp/amp1/debasd -f $(ls -t basd* | head -1) -s $(expr $(/usr/local/amp/amp1/debasd -l -f $(ls -t basd* | head -1) 2>&1 | cut -d' ' -f3) - 10)''').read()
print(type(debasd))

f = "/home/newtec/debasd.txt"

with open(f,"a") as file:
        file.write(debasd)
