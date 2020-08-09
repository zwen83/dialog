# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/2/29
from time import sleep
import datetime
import json
import csv
import influxdb
import configparser
import logging
from logging.handlers import RotatingFileHandler
loggingFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
dateFormat    = '%d/%m/%Y %H:%M:%S'
formatter     = logging.Formatter(loggingFormat, datefmt=dateFormat)
logger        = logging.getLogger('')
logger.setLevel(logging.DEBUG)
from rest import REST



def GetAllModems(rest, iQtyPerTurn=300):
    params = {'property': ['macAddress', 'id', 'locked', 'satelliteNetworkConfigurations', 'satelliteNetworkId']}
    params['start'] = 0
    params['limit'] = iQtyPerTurn

# a cycle for reading iQtyPerTurn modems per request in order not to overload the CMS
    modems = list()
    bGetMore = True
    while bGetMore:
        logger.info('GET CMS modems from %i to %i' % (params['start'] + 1, params['start'] + params['limit']))
        try:
            modemsPart = rest.GET('modem/collect', params=params)
        except REST.ConnectionError:
            logger.critical('Error connecting to the hub')
            break
        except REST.AuthorizationError:
            logger.critical('Check credentials in the .ini file')
            break
        except KeyboardInterrupt:
            print('Keyboard interrupt')
            exit(0)
        if not modemsPart or type(modemsPart) != list:
            logger.warning('GET CMS modems from %i to %i failed' % (params['start'] + 1, params['start'] + params['limit']))
            bGetMore = False
        else:
# if a correct reply was received add those modems to the list
            logger.debug('Adding retrieved modems to the list')
            modems.extend(modemsPart)
# if modems count is 100, then probably there are more modems in CMS, continue the cycle
            if len(modemsPart) == params['limit']:
                params['start'] += params['limit']
            else:
                bGetMore = False
    for modem in modems:
        modem['satnet'] = modem['satelliteNetworkId']['name'] if 'satelliteNetworkId' in modem else modem['satelliteNetworkConfigurations'][0]['satelliteNetworkId']['name'] if ('satelliteNetworkConfigurations' in modem and modem['satelliteNetworkConfigurations'][0]['satelliteNetworkId']) else ''
    return modems