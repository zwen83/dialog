#!/usr/bin/env python3
# -*- coding: utf-8 -*-

loggingFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
dateFormat    = '%d/%m/%Y %H:%M:%S'

__author__ = 'isim'
__version__ = 1.0

from optparse import OptionParser
from time import sleep
import csv
import logging
import json

try:
    import rest as REST
except ImportError:
    print('The module REST is used as an external module. The file rest.py or rest.pyc needs to be placed in the same directory.')
    exit(1)

def SetLogging(loggingLevel, loggingFormat, dateFormat, log):
    formatter = logging.Formatter(loggingFormat, datefmt=dateFormat)
    logger = logging.getLogger('CollectODU')
    logger.setLevel(logging.DEBUG)
    if log:
        fH = logging.FileHandler(log)
        fH.setLevel(logging.DEBUG)
        fH.setFormatter(formatter)
        logger.addHandler(fH)
    cH = logging.StreamHandler()
    cH.setLevel(loggingLevel)
    cH.setFormatter(formatter)
    logger.addHandler(cH)
    return logger

def ParseCommandLine():
    usage = "usage: %prog options"
    parser = OptionParser(usage)
    parser.add_option("-i", "--ip", dest="ip", help="IP of a Dialog", metavar="IP")
    parser.add_option("-u", "--username", dest="username", help="Username to login to a Dialog", metavar="USERNAME", default = "hno")
    parser.add_option("-p", "--password", dest="password", help="Password to login to a Dialog", metavar="'PASSWORD'", default = "D!@10g")
    parser.add_option("-s", "--satnet", dest="satnet", help="SATNET which modems to process", metavar="SATNET")
    parser.add_option("-o", "--output", dest="filename", help="write processed modems to FILE", metavar="FILE")
    parser.add_option("-x", "--exclude", dest="exclude", help="FILE with modems to exclude or previously processed modems", metavar="FILE")
    parser.add_option("-l", "--log", dest="log", help="FILE where to store the log", metavar="FILE")
    (options, args) = parser.parse_args()
    if not options.ip:
        print('Dialog IP or IP:PORT should be provided, use --help for help')
        exit(1)
    return options

def ConnectToDialog(ip, username, password):
    try:
        rest = REST.REST(ip, username, password)
    except:
        rest = False
    return rest

def GetAllModems(rest, satnet):
    params = dict()
    if satnet:
        params['satelliteNetworkName'] = satnet
    else:
        logger.debug('Satnet is not defined, getting all satnets from the hub')
        satnets = GetSatnets(rest)
        if len(satnets) != 1:
            print('The Satnet is configured wrong. There are %i Satnets available:' % len(satnets))
            for satnet in satnets:
                print(satnet['name'])
            exit(1)
        else:
            logger.debug('%s will be used, as it is the only satnet in the hub.', satnets[0])
            params['satelliteNetworkName'] = satnets[0]
    
    params['property'] = ['macAddress', 'id', 'locked', 'remoteGuiUrl']
    params['start'] = 0
    params['limit'] = 100
    modems = list()
    bGetMore = True
    while bGetMore:
        logger.info('GET CMS modems from %i to %i' % (params['start'] + 1, params['start'] + params['limit']))
        try:
            modemsPart=rest.GET('modem/collect', params=params)
        except REST.ConnectionError:
            logger.critical('Error connecting to the hub')
            exit(1)
        except REST.AuthorizationError:
            logger.critical('Check credentials in the .ini file')
            exit(1)
        if not modemsPart or type(modemsPart) != list:
            logger.warning('GET CMS modems from %i to %i failed' % (params['start'] + 1, params['start'] + params['limit']))
            bGetMore = False
        else:
# if a correct reply was received add those modems to the list
            logger.debug('Adding retrieved modems to the list')
            modems.extend(modemsPart)
# if modems count is 100, then probably there are more modems in CMS, continue the cycle
            if len(modemsPart) == 100:
                params['start'] += params['limit']
            else:
                bGetMore = False
    if len(modems) == 0:
        logger.error('GET modems from CMS failed')
        satnets = GetSatnets(rest)
        print('The Satnet is configured wrong. There are %i Satnets available:' % len(satnets))
        for satnet in satnets:
            print(satnet['name'])
        exit(1)
    return modems

def GetSatnets(rest):
    try:
        satnets = rest.GET('satellite-network/collect', params={'property':'name'})
    except:
        logger.error('Failed while getting Satnets from CMS')
        exit(1)
    return satnets

def ExcludeModems(modems, filename):
    if not (modems and type(modems) == list and len(modems) > 0):
        logger.error('No modems to process')
        exit(1)
# convert a modem list to a dict for better performance
    modemsDict = dict()
    for modem in modems:
        modemsDict[modem['macAddress']]= modem
    try:
        logger.debug('Reading modems from the exclude file %s' % filename)
    except KeyError:
        logger.info('No exclude modems file defined. All modems will be processed.')
        modemsToProcess = modems
    else:
        try:
            fR = open(filename)
            reader = csv.DictReader(fR)
            if not reader.fieldnames or 'MacAddress' not in reader.fieldnames:
                logger.warning('An exclude file should contain a column with "MacAddress" header. All modems will be processed.')
                return modems 
            for row in reader:
                if row['MacAddress'] in modemsDict: 
                    logger.debug('Removing MacAddress %s from the to-process list' % row['MacAddress'])
                    modemsDict.pop(row['MacAddress'])
        except (OSError, IOError):
            logger.error('Error reading modems from the file %s. All modems will be processed.' % filename)
            modemsToProcess = modems
# convert the modems dict back to a list
        else:
            modemsToProcess = list()
            for key in modemsDict:
                modemsToProcess.append(modemsDict[key])
    return modemsToProcess

def SendJSONRequest(rest, url, functionName, params = ''):
    result = False
    urlParams = {'request':'{"FunctionName":"%s"%s}' % (functionName, (', "Params": %s' % json.dumps(params)  if params else ''))}
    logger.debug('Sending %s %s', functionName, ('with Params: %s' % params if params else ''))
    try:
        reply = rest.GET('cgi-bin/cgiclient', '', url, params=urlParams)
    except REST.ConnectionError:
        logger.critical('Network connection error')
        exit(1)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    logger.debug('Received reply: %s', reply)
    try:
        if reply['RequestResult']['Success']:
            if 'RequestData' in reply:
                result = reply['RequestData']
            else:
                result = True
    except KeyError:
        logger.debug('Reply is corrupted')
        result = False
    except TypeError:
        result = False
    return result

def ProcessAndWriteModems(modemsToProcess, rest, filename):
    if not (modemsToProcess and type(modemsToProcess) == list and len(modemsToProcess) > 0):
        logger.warning('No modems to process')
        exit(1)
    logger.warning('The number of modems to process: %i', len(modemsToProcess))
    writer = None
# try to open a file to write the processed modems
    if not filename:
        logger.warning('Output file is not defined')
    else:
        logger.debug('Opening file %s for writing (append)' % filename)
        try:
            fW = open(filename, 'a')
            writer = csv.DictWriter(fW, ['id', 'name', 'MacAddress', 'BUC LO'])
            if fW.tell() == 0:
                writer.writeheader()
        except (OSError, TypeError):
            logger.error('Error opening processed modems file %s' % filename)
            writer = ''
    try:
        for modem in modemsToProcess:
            if modem['locked']:
                logger.debug('The modem %s is locked' % (modem['macAddress']))
                continue
            logger.debug('Processing the modem %s (%s)' % (modem['macAddress'], modem['id']['name']))
            result = SendJSONRequest(rest, modem['remoteGuiUrl'], 'GetActiveODUType')
            try:
                activeODUTypeId = result['ODUTypeId']
                result = SendJSONRequest(rest, modem['remoteGuiUrl'], 'GetODUTypeData', {'ODUTypeId':activeODUTypeId})
                if 'BUCData' in result and result['BUCData']:
                    if writer:
                        writer.writerow({'MacAddress' : modem['macAddress'], 'id': modem['id']['systemId'], 'name': modem['id']['name'], 'BUC LO': result['BUCData']['LO']})
                    logger.info('LO of the modem %s is %s' % (modem['macAddress'], result['BUCData']['LO'])) 
                else:
                    logger.info("The modem %s doesn't contain BUC data" % modem['macAddress'])
            except (TypeError, KeyError):
                logger.error('Error fetching BUC LO data from the modem %s' % modem['macAddress'])
    except (OSError, TypeError):
        logger.error('Error writing modems to the file')
        exit(1)
    except REST.ConnectionError:
        logger.critical('Error connecting to the hub')
        exit(1)
    except REST.AuthorizationError:
        logger.critical('Check credentials to access the hub')
        exit(1)


if __name__=='__main__':
    print('A script for collecting ODU info of all modems in a certain Satnet v%3.1f\n' % __version__)
    options = ParseCommandLine()
    logger = SetLogging(logging.INFO, loggingFormat, dateFormat, options.log)
    logger.warning('**** Start of the log ****')
    rest = ConnectToDialog(options.ip, options.username, options.password)
    if not rest:
        print('ERROR: Connection to the hub cannot be established, check IP, USERNAME and PASSWORD')
        exit(1)
    modems = GetAllModems(rest, options.satnet)
    modemsToProcess = ExcludeModems(modems, options.exclude) if options.exclude else modems
    ProcessAndWriteModems(modemsToProcess, rest, options.filename)
    logger.warning('**** End of the log ****')

