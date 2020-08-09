# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/7/2

from rest import REST
import gevent
from gevent import monkey
monkey.patch_all(thread=False)
import multiprocessing
from DialogAPI import DialogAPI
import csvhandler
import modemparser


def terminalGroup(self, modeminfoList, hubs):
    gevent.joinall([gevent.spawn(self.terminalParser, modem, hubs) for modem in modeminfoList])
'''
combine with gevent , use multiprocess pool will be more efficient, for my PC is 8 core, so I use 8.  one core for 100 terminals.
'''

if __name__ == '__main__':
    FILE = 'Modem_info.csv'
    csvhandler.writeHeader()
    filename = 'mac.csv'
    macList = csvhandler.ReadCsv(filename)
    host = '10.0.10.60'
    user = 'hno'
    password = '=kQ9+bQ(B+kh2NbD'
    a = DialogAPI(host,user,password)
    modeminfoList = a.getModem(macList)
    print(modeminfoList)
    hubs = a.gethubmodule()
    # for modeminfo in modeminfoList:
    #     gevent.joinall([gevent.spawn(modemparser.modemParser,modem,hubs,host,user,password) for modem in modeminfo])

    pp = multiprocessing.Pool(8)
    for modem in modeminfoList:
        pp.apply_async(modemparser.modemParser(modem[0],hubs,host,user,password))
    pp.close()
    pp.join()

