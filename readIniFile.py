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

try:
    import rest as REST
except ImportError:
    print('The module REST is used as an external module. The file rest.py or rest.pyc needs to be placed in the same directory.')
    exit(1)
if REST.__version__ < 2.2:
    print('The file rest.py should be v2.2 or higher')
    exit(1)

nonPlatforms = ['Logging', 'DB', 'Other', 'DEFAULT']
def ReadConfig(iniFilename):
    global formatter, logger
    try:
        configuration = configparser.ConfigParser()
        configuration.optionxform = lambda option: option
        try:
            configuration.read(iniFilename)
        except (configparser.DuplicateOptionError, configparser.ParsingError) as Err:
            print('ERROR:', Err)
            exit(1)
        if len(configuration) < 2:
            print('%s file not found' % iniFilename)
            exit(1)
# check for obligitary settings in the .ini file
        config = dict()
        for section in configuration:
            config[section] = dict()
            for key in configuration[section]:
                config[section][key] = configuration[section][key]
        for section in config:
            if section in nonPlatforms:
                continue
            for attr in ['cmsip']:
                if attr not in config[section]:
                    print('Non-empty values of %s should be presented in the platform access section named "%s" of the .ini file' % (attr, section))
                    exit(1)

# configure logging of the script
        maxBytes    = GetUnsignedFromConfig(config, 'Logging', 'maxBytes')
        backupCount = GetUnsignedFromConfig(config, 'Logging', 'logFilesCount')
        if 'Logging' in config:
            if 'logfile' in config['Logging'] and config['Logging']['logfile']:
                fH = RotatingFileHandler(config['Logging']['logfile'], maxBytes=maxBytes, backupCount=backupCount)
                fH.setLevel(logging.DEBUG)
                fH.setFormatter(formatter)
                logger.addHandler(fH)
            loggingLevel = logging.WARNING
            if 'loggingLevel' in config['Logging'] and config['Logging']['loggingLevel']:
                loglevel = config['Logging']['loggingLevel'].upper()
                if 'DEBUG' in loglevel:
                    loggingLevel = logging.DEBUG
                elif loglevel == 'INFO':
                    loggingLevel = logging.INFO
                elif loglevel == 'WARNING':
                    loggingLevel = logging.WARNING
                elif loglevel == 'ERROR':
                    loggingLevel = logging.ERROR
                elif loglevel == 'CRITICAL':
                    loggingLevel = logging.CRITICAL
            cH = logging.StreamHandler()
            cH.setLevel(loggingLevel)
            cH.setFormatter(formatter)
            logger.addHandler(cH)
            if loglevel == 'FULLDEBUGWITHREST':
                logging.getLogger('rest').setLevel(logging.DEBUG)
    except OSError:
        print('Reading config file failed')
        exit(1)
    logger.debug('Config file has been read')
    return config


def GetUnsignedFromConfig(config, section, key, default=0):
    try:
        result = int(config[section][key])
        if result < 0:
            raise ValueError
    except KeyError:
        result = default
    except ValueError:
        print('%s should be an unsigned integer number in the .ini file' % key)
        exit(1)
    return result


path = r"C:\Users\zwen.073111-PC\dialog\Dialog2TSDB.ini"
print(ReadConfig(path))