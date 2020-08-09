# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/2/26


from rest import REST

ip = '192.168.48.230'
username = 'hno'
password = 'D!@10g'

rest = REST(ip, username, password)

print('Reading modems database...')
modems = rest.GET('modem')
print (modems)


print('%i modems read' % len(modems))
for modem in modems:
    if not modem['locked']:

        print('- modem name: %s - %s' %(modem['id']['name'], modem['returnTechnology']))
hubmodule = rest.GET('hub-module')


print(type(hubmodule))

hubmoduleDict = hubmodule[0]

hubmoduleName = hubmoduleDict['devicePools'][0]['hubModuleId']['name']
satnetID = hubmoduleDict['devicePools'][0]['hpsId']
hubModuleType = hubmoduleDict['hubModuleType']

print (hubModuleType)

print('Done')
