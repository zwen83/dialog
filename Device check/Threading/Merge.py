# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/27


def Merge(dict1, dict2):
    return (dict2.update(dict1))

d1 = {'RTN Total bitrate': 83946, 'RTN Drop bitrate': 0}

d2 = {'Satnet': 6, 'Hub Name': 'KAC_JAV-1', 'time': '2020-05-27T06:34:55.366441', 'FWD Drop bitrate': 0, 'FWD Total bitrate': 1028587}


print(Merge(d1,d2))
print(d1.update(d2))

dictMerged=d1.copy()
dictMerged.update(d2)

print(dictMerged)