#!/usr/bin/env python3
# -*- coding: utf-8 -*-

iniFilename = 'Asia HUB.ini'

__author__ = 'isim'
__version__ = 5.0

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


#--------------------------------------------------------------------------#
#------ Procedure for reading config from an .ini file --------------------#
#--------------------------------------------------------------------------#
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
            logger.debug('**** Log start of %s v.%3.1f ****' % (__name__, __version__))
            if loglevel == 'FULLDEBUGWITHREST':
                logging.getLogger('rest').setLevel(logging.DEBUG)
    except OSError:
        print('Reading config file failed')
        exit(1)
    logger.debug('Config file has been read')
    return config


def GetBooleanFromConfig(config, section, key, default=False):
    try:
        if config[section][key].lower() == 'true' or config[section][key].lower() == 'yes':
            result = True
        elif config[section][key].lower() == 'false' or config[section][key].lower() == 'no':
            result = False
        else:
            print('The value %s should be true/false or yes/no' % key)
            exit(1)
    except KeyError:
        result = default
    return result


def GetStrFromConfig(config, section, key, default=''):
    try:
        result = config[section][key]
    except KeyError:
        result = default
    return result


def GetIntFromConfig(config, section, key, default=0):
    try:
        result = int(config[section][key])
    except KeyError:
        result = default
    except ValueError:
        print('%s should be an integer number in the .ini file' % key)
        exit(1)
    return result


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


def GetFloatFromConfig(config, section, key, default=0):
    try:
        result = float(config[section][key])
    except KeyError:
        result = default
    except ValueError:
        print('%s should be a float number in the .ini file' % key)
        exit(1)
    return result


#--------------------------------------------------------------------------#
#------ Procedure for reading all modems from CMS -------------------------#
#--------------------------------------------------------------------------#
def GetAllModems(rest, iQtyPerTurn=300):
    params = {'property': ['macAddress', 'id', 'locked', 'satelliteNetworkConfigurations', 'satelliteNetworkId', 'attachment', 'serviceProfileId']}
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
        modem['satnet'] = modem['satelliteNetworkId']['name'] if 'satelliteNetworkId' in modem and type(modem['satelliteNetworkId']) == dict and 'name' in modem['satelliteNetworkId'] else modem['satelliteNetworkConfigurations'][0]['satelliteNetworkId']['name'] if 'satelliteNetworkConfigurations' in modem and type(modem['satelliteNetworkConfigurations']) == list and len(modem['satelliteNetworkConfigurations']) == 1 and type(modem['satelliteNetworkConfigurations'][0]) == dict and 'satelliteNetworkId' in modem['satelliteNetworkConfigurations'][0] and type(modem['satelliteNetworkConfigurations'][0]['satelliteNetworkId']) == dict and 'name' in modem['satelliteNetworkConfigurations'][0]['satelliteNetworkId'] else modem['attachment']['satelliteNetworkId']['name'] if 'attachment' in modem and type(modem['attachment']) == dict and 'satelliteNetworkId' in modem['attachment'] and type(modem['attachment']['satelliteNetworkId']) == dict else ''
    return modems

#--------------------------------------------------------------------------#
#------ InfluxDB  utilities -----------------------------------------------#
#--------------------------------------------------------------------------#
def connectToDB(host='localhost', port=8086, username='root', password='root'):
    global influxDBClient, logger
    influxDBClient = influxdb.InfluxDBClient(host=host, port=port, username=username, password=password)
    try:
        if not influxDBClient.ping():
            logger.critical('Cannot connect to the TSDB')
            exit(1)
    except:
        logger.exception('Exception while connecting to the TSDB')
        exit(1)
    return influxDBClient


def CheckDBs(influxDBClient, DBs2check, platform):
    global logger
    try:
        ExistingDBs = influxDBClient.get_list_database()
        DBs = [DB['name'] for DB in ExistingDBs]
        for db in DBs2check:
            if db not in DBs:
                influxDBClient.create_database(db)
                influxDBClient.create_retention_policy('realtime', GetStrFromConfig(config, platform, 'realtimeDataPeriod', '90d'), 1, database=db, default=True)
                influxDBClient.create_retention_policy('archive', GetStrFromConfig(config, platform, 'archivePeriod', '52w'), 1, database=db, default=False)
                logger.debug('"%s" DB was created' % db)
    except:
        logger.exception('Exception while creating the needed DBs')
        exit(1)

def WriteToDB(DB, pointList):
    try:
        result = influxDBClient.write_points(pointList, database=DB)
        if not result:
            logger.error('Error during writing to the "%s" DB' % DB)
    except influxdb.exceptions.InfluxDBClientError:
        logger.exception('Exception during writing to the "%s" DB' % DB)
        return False
    except:
        logger.exception('Exception during writing to the "%s" DB' % DB)
        return False
    return True


def addPoint(pointList, measurement, value, terminal, now, platform, additionalFields=None):
    fields = {'value': value}
    if additionalFields:
        fields.update(additionalFields)
    pointList.append({'fields': fields, 'measurement': measurement, 'tags': 
        {'satnet': terminal['satnet'], 'platform': platform, 'modem_name': terminal['id']['name'], 'modem_id': terminal['id']['systemId'], 
         'vno_name': terminal['id']['domainName'], 'vno_id': terminal['id']['domainId'], 
         'fwd_pool_name': terminal['attachment']['forwardPoolId']['name'], 'fwd_pool_id': terminal['attachment']['forwardPoolId']['systemId'],
         'rtn_pool_name': terminal['attachment']['returnPoolId']['name'], 'rtn_pool_id': terminal['attachment']['returnPoolId']['systemId'],
        }, 'time': now})


#--------------------------------------------------------------------------#
#------ Procedures for connecting to a Dialog hub -------------------------#
#--------------------------------------------------------------------------#
def GetOplog(rest):
    global logger
    currentOplog = 1
    auth = rest._auth
    cookies = rest.cookies
    rest.cookies = None
    rest._auth = ('poller', 'dialog')
    try:
        oplogs = rest.GET('oplog')
    except REST.DialogError as e:
        if 'NOT_FOUND' in e.args[0]:
            currentOplog = 0
        else:
            logger.exception('Exception while collecting oplog')
            currentOplog = -1
    except REST.ConnectionError:
        currentOplog = -2
    except:
        logger.exception('Exception while collecting oplog')
        currentOplog = -1
    else:
        if oplogs:
            for oplog in oplogs:
                if oplog['scope'] == 'Global':
                    currentOplog = int(oplog['lastModifiedEpoch'])
                    break
            logger.debug('Current oplog = %i' % currentOplog)
        else:
            currentOplog = 0
    finally:
        rest._auth = auth
        rest.cookies = cookies
    return currentOplog


def ConnectToDialog(config, platform):
    global logger
    rest = None
    try:
        rest = REST.REST(config[platform]['cmsip'],
                         config[platform]['username'] if 'username' in config[platform] else config['username'] if 'username' in config else 'poller',
                         config[platform]['password'] if 'password' in config[platform] else config['password'] if 'password' in config else 'dialog')
        if not rest:
            logger.critical('Error during connecting to the hub')
            exit(1)
    except:
        logger.critical('Error during connecting to the hub')
        exit(1)
    return rest


def GetHubmodules(rest):
    global logger
    hubmodules = None
    try:
        hubmodules = rest.GET('hub-module/collect?property=id&property=locked&property=hubModuleType&property=enclosures&property=physicalSatNets')
    except:
        logger.exception('Exception while fetching hubmodule info:')
    return hubmodules
#--------------------------------------------------------------------------#
#------ Save Stats to DB --------------------------------------------------#
#--------------------------------------------------------------------------#
def GetCPMControllerUrls(hubmodules):
    urls = list()
    for hm in hubmodules:
        if 'locked' in hm and hm['locked']:
            continue
        if 'physicalSatNets' in hm:
            for sn in hm['physicalSatNets']:
                if 'hubModuleType' in hm:
                    for i in range(1,5):
                        urls.append('/remote-gui/%s%s/cpmctl-%i/amp%i' % (hm['id']['name'], '' if '4IF' == hm['hubModuleType'] else '_ENCL-1', sn['hpsId'] if 'hpsId' in sn else sn['if'], i))
    return urls


def GetHRCControllerUrls(hubmodules):
    urls = list()
    for hm in hubmodules:
        if 'locked' in hm and hm['locked']:
            continue
        if 'physicalSatNets' in hm:
            for sn in hm['physicalSatNets']:
                if 'hubModuleType' in hm:
                    urls.append('/remote-gui/%s/HMGW-0%s/hrccontroller-%i/statistics' % (hm['id']['name'], '-0' if '4IF' == hm['hubModuleType'] else '', sn['hpsId'] if 'hpsId' in sn else sn['if']))
    return urls


def saveHRCstate(platform, rest, hrcctls, allmodems):
    global logger
    CheckDBs(influxDBClient, ['HRC', 'Terminals'], platform)
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %T')

    try:
        with open('HRC ModCods') as fR:
            HRCModCods = json.load(fR)
    except:
        logger.exception('Exception while loading "HRC ModCods" file')
        exit(1)
    HRCModCodsDict = dict()
    for HRCModCod in HRCModCods:
        HRCModCodsDict[HRCModCod['id']] = HRCModCod['displayName']

    modemsDict = dict()
    for modem in allmodems:
        modemsDict[modem['id']['systemId']] = modem

    for url in hrcctls:
        try:
            stats = rest.GET(url, '', '')
            if not stats:
                continue
        except:
            continue
        savestats(platform, stats, modemsDict, HRCModCodsDict, now)


def savestats(platform, stats, modemsDict, HRCModCodsDict, now):
    global logger
    pointList = list()
    for transponder in stats['transponders']:
        pointList.append({'fields': {'value': stats['transponders'][transponder]['translationFrequencyOffsetAvg']},
                          'measurement': 'Transponder Offset',
                          'tags': {'name': stats['transponders'][transponder]['name'], 'platform': platform},
                          'time': now})
    for rcg in stats['carrierGroups']:
        pointList.append({'fields': {'value': stats['carrierGroups'][rcg]['allocatedRate']['value']},
                          'measurement': 'Allocated Rate', 'tags': {'name': rcg, 'platform': platform}, 'time': now})
        for KPI in [('availableBandwidth', 'Available Bandwidth'), ('bbpEfficiency', 'BBP Efficiency'), ('loggedOnTerminals', 'LoggedOn Terminals'), ('physicalLayerEfficiency', 'Physical Layer Efficiency'), ('usedBandwidth', 'Used Bandwidth')]:
            if stats['carrierGroups'][rcg][KPI[0]]:
                pointList.append({'fields': {'value': stats['carrierGroups'][rcg][KPI[0]]}, 'measurement': KPI[1], 'tags': {'name': rcg, 'platform': platform}, 'time': now})
    if WriteToDB('HRC', pointList):
        logger.debug(platform + ': Successfully exported to "HRC"')
    else:
        logger.error(platform + ': Error while exporting to "HRC"')

    modemStates = ['Unknown', 'Idle', 'Waiting', 'LoggingOn', 'Acquiring', 'Syncing', 'LoggedOn', 'Scheduling', 'LogOnFailed', 'Stopping']
    signalStates = ['Unknown', 'Ok', 'NoSignal', 'TxPowerTooHigh']

    pointList.clear()
    terminals = dict()
    for rcg in stats['carrierGroups']:
        terminals.update(stats['carrierGroups'][rcg]['terminals'])
    for terminalId in terminals:
        terminal = terminals[terminalId]
        Id = terminalId.split('_')[1] if '_' in terminalId else terminalId
        addPoint(pointList, 'HRC State', modemStates.index(terminal['state']) if terminal['state'] in modemStates else 0, modemsDict[int(Id)], now, platform, {'description': terminal['state']})
        for KPI in [('Frequency', 'frequency'), ('Frequency Offset', 'frequencyOffset'), ('TX Power', 'txPower')]:
            addPoint(pointList, KPI[0], terminal[KPI[1]]['value'], modemsDict[int(Id)], now, platform)
        if terminal['state'] == 'LoggedOn':
            for KPI in [('HRC Es/N0', 'esNo'), ('HRC CoND', 'coND'), ('HRC RX Power', 'rxPower')]:
                addPoint(pointList, KPI[0], terminal['receiveInfo'][KPI[1]]['value'], modemsDict[int(Id)], now, platform)
            for KPI in terminal['receiveInfo']:
                if type(terminal['receiveInfo'][KPI]) == dict and KPI not in ['esNo', 'coND', 'rxPower']:
                    addPoint(pointList, 'HRC ' + KPI, terminal['receiveInfo'][KPI]['value'], modemsDict[int(Id)], now, platform)
            addPoint(pointList, 'HRC Bitrate', terminal['bitrate']['value'], modemsDict[int(Id)], now, platform)
            addPoint(pointList, 'HRC Signal Status', signalStates.index(terminal['receiveInfo']['signalStatus']) if terminal['receiveInfo']['signalStatus'] in modemStates else 0, modemsDict[int(Id)], now, platform, {'description': terminal['receiveInfo']['signalStatus']})
            addPoint(pointList, 'HRC Insufficient Guard Band', int(terminal['receiveInfo']['insufficientGuardBand']), modemsDict[int(Id)], now, platform)
            addPoint(pointList, 'HRC Symbol Rate', terminal['symbolRate'], modemsDict[int(Id)], now, platform)
            addPoint(pointList, 'HRC ModCod', terminal['modcod'], modemsDict[int(Id)], now, platform, {'description': HRCModCodsDict[terminal['modcod']]})
            addPoint(pointList, 'HRC Regrowth Limited Power', terminal['regrowthLimitedPower'], modemsDict[int(Id)], now, platform)
            addPoint(pointList, 'TX Frequency Correction', terminal['termTxFrequencyCorrection'], modemsDict[int(Id)], now, platform)
    if WriteToDB('Terminals', pointList):
        logger.debug(platform + ': Successfully exported HRC to "Terminals"')
    else:
        logger.error(platform + ': Error while exporting HRC to "Terminals"')


def GetPerformanceUrls(hubmodules, iCount=1, now=datetime.datetime.utcnow()):
    if not hubmodules:
        return None
    filenames = list()
    now = now - datetime.timedelta(seconds=60)
    for i in range(iCount):
        filenames.append('performance_%s%02i.csv' % (now.strftime('%Y%m%d%H'), now.minute - now.minute % 5))
        now = now - datetime.timedelta(seconds=300)
    filenames.reverse()
    urls = list()
    for hm in hubmodules:
        if 'locked' in hm and hm['locked']:
            continue
        if 'hubModuleType' in hm:
            if 'NMS' in hm['hubModuleType']:
                continue
            elif 'XIF' in hm['hubModuleType']:
                if 'XIF Processing HM' == hm['hubModuleType']:
                    for encl in hm['enclosures']:
                        if 'type' in encl and encl['type'] == 'ENCLOSURE':
                            url = '/remote-gui/%s_ENCL-%i/HMGW-0-0/mc/performance/' % (hm['id']['name'], encl['slotId'])
                            for filename in filenames:
                                urls.append(url + filename)
            else:
                url = '/remote-gui/%s/HMGW-0%s/mc/performance/' % (hm['id']['name'], '-0' if '4IF' == hm['hubModuleType'] else '')
                for filename in filenames:
                    urls.append(url + filename)
        else:
            url = '/remote-gui/hm-%i/HMGW-0/mc/performance/' % hm['id']['systemId']
            for filename in filenames:
                urls.append(url + filename)
    return urls

def getfloat(s, default=0.0):
    return getnumber(s, float, default)
def getint(s, default=0):
    return getnumber(s, int, default)
def getnumber(s, numberType, default):
    if not s:
        return default
    try:
        result = numberType(s)
    except ValueError:
        result = default
    return result

def ParsePerformance(platform, rest, urls, allmodems, fillQoSGapsWithZeroes=False):
    global logger
    CheckDBs(influxDBClient, ['Dialog_totals', 'Terminals'], platform)

    modemsDict = dict()
    satnets = dict()
    for modem in allmodems:
        modemsDict[modem['id']['systemId']] = modem
        if modem['satnet'] not in satnets:
            satnets[modem['satnet']] = dict()
            for direction in ['FWD', 'RTN']:
                satnets[modem['satnet']][direction] = dict()
                for qos in ['BE', 'CD1', 'CD2', 'CD3', 'RT1', 'RT2', 'RT3', 'Total']:
                    satnets[modem['satnet']][direction][qos] = 0

    pointList = list()
    for url in urls:
        try:
            logger.info(platform + ': Processing %s' % url)
            performanceFile = rest.GETFILE(url)
            if not performanceFile:
                logger.error(platform + ': No Performance file got at %s' % url)
                continue
            performance = csv.DictReader(performanceFile.split('\r\n'))
            print (type(performanceFile))
        except:
            logger.exception(platform + ': Exception during getting the performance file "%s"' % url)
        else:
            date = url.split('.')[0].split('_')[-1]
            now = date[0:4] + '-' + date[4:6] + '-' + date[6:8] + ' ' + date[8:10] + ':' + date[10:12] + ':00'
            for satnet in satnets:
                for direction in ['FWD', 'RTN']:
                    for qos in ['BE', 'CD1', 'CD2', 'CD3', 'RT1', 'RT2', 'RT3', 'Total']:
                        satnets[satnet][direction][qos] = 0
            for row in performance:
                print(row)
                modemId = int(row['Modem id'])
                addPoint(pointList, 'FWD Es/N0', getfloat(row['Forward Es/N0 average']), modemsDict[modemId], now, platform, {'min': getfloat(row['Forward Es/N0 minimum']), 'max': getfloat(row['Forward Es/N0 maximum'])})
                if row['Return C/N0 average']:
                    addPoint(pointList, 'RTN C/N0', getfloat(row['Return C/N0 average']), modemsDict[modemId], now, platform, {'min': getfloat(row['Return C/N0 minimum']), 'max': getfloat(row['Return C/N0 maximum'])})
                for direction in [('Forward', 'FWD'), ('Return', 'RTN')]:
                    totalTerminal = 0
                    for qos in ['BE', 'CD1', 'CD2', 'CD3', 'RT1', 'RT2', 'RT3']:
                        value = row['%s throughput %s' % (direction[0], qos)]
                        if value:
                            iValue = getint(value)
                            addPoint(pointList, '%s %s Throughput' % (direction[1], qos), iValue, modemsDict[modemId], now, platform)
                            totalTerminal += iValue
                            satnets[modemsDict[modemId]['satnet']][direction[1]][qos] += iValue
                        elif fillQoSGapsWithZeroes:
                            addPoint(pointList, '%s %s Throughput' % (direction[1], qos), 0, modemsDict[modemId], now, platform)
                    addPoint(pointList, '%s Total Throughput' % direction[1], totalTerminal, modemsDict[modemId], now, platform)
                    satnets[modemsDict[modemId]['satnet']][direction[1]]['Total'] += totalTerminal
                    if len(pointList) > 5000:
                        if not WriteToDB('Terminals', pointList):
                            logger.error(platform + ': Error while exporting to the TSDB "Terminals"')
                        sleep(1)
                        pointList.clear()

            if WriteToDB('Terminals', pointList):
                logger.debug(platform + ': Successfully exported to "Terminals"')
            else:
                logger.error(platform + ': Error while exporting to "Terminals"')
            pointList.clear()
            for satnet in satnets:
                for direction in ['FWD', 'RTN']:
                    for qos in ['BE', 'CD1', 'CD2', 'CD3', 'RT1', 'RT2', 'RT3', 'Total']:
                        pointList.append({'fields': {'value': satnets[satnet][direction][qos]}, 'tags': {'platform': platform, 'satnet': satnet}, 'measurement': '%s %s Throughput' % (direction, qos), 'time': now})
            if WriteToDB('Dialog_totals', pointList):
                logger.debug(platform + ': Successfully exported totals to "Dialog_totals"')
            else:
                logger.error(platform + ': Error while exporting totals to "Dialog_totals"')
            sleep(3)
    print(pointList)
    return pointList


#--------------------------------------------------------------------------#
#------ Cache -------------------------------------------------------------#
#--------------------------------------------------------------------------#
import pickle
def savecache(cacheFilename, *v):
    global logger
    try:
        with open(cacheFilename, 'wb') as fW:
            for obj in v:
                pickle.dump(obj, fW)
    except:
        logger.exception('Exception while saving cache')
        return False
    return True

def loadcache(cacheFilename):
    global logger
    result = list()
    i = 0
    try:
        with open(cacheFilename, 'rb') as fR:
            while True:
                result.append(pickle.load(fR))
                i += 1
    except EOFError:
        logger.debug('Cache loaded %i objects' % i)
    except FileNotFoundError:
        logger.debug('No cache file found')
    except:
        logger.exception('Exception while loading cache')
    return result


def ProcessPlatform(config, platform):
    global logger
    rest = ConnectToDialog(config, platform)
    currentOplog = GetOplog(rest)
    if currentOplog < 0:
        logger.critical('Cannot connect to the platform ' + platform)
        return False
    allmodems = None
    hubmodules = None
    if currentOplog > 0:
        try:
            prevOplog, prevallmodems, prevhubmodules = loadcache(platform + '.Dialog2TSDB.cache')
        except:
            prevOplog = 0
            prevallmodems = list()
            prevhubmodules = list()
        if currentOplog == prevOplog:
            allmodems = prevallmodems
            hubmodules = prevhubmodules
    if not allmodems:
        logger.debug(platform + ': Oplog is different, reading all the hub info')
        allmodems = GetAllModems(rest, 500)
        if not allmodems:
            logger.error('Error reading modems for %s' % platform)
            return False
    if not hubmodules:
        hubmodules = GetHubmodules(rest)
        if not hubmodules:
            logger.error('Error reading hubmodules for %s' % platform)
            return False
    if currentOplog > 0:
        savecache(platform + '.Dialog2TSDB.cache', currentOplog, allmodems, hubmodules)

    urls = GetPerformanceUrls(hubmodules, GetIntFromConfig(config, platform, 'performanceFilesCount', 3))
    ParsePerformance(platform, rest, urls, allmodems, GetBooleanFromConfig(config, platform, 'fillQoSGapsWithZeroes', False))
    if GetBooleanFromConfig(config, platform, 'parseHRC', False):
        hrcctls = GetHRCControllerUrls(hubmodules)
        saveHRCstate(platform, rest, hrcctls, allmodems)
    return True
#--------------------------------------------------------------------------#
#------ The entry point ---------------------------------------------------#
#--------------------------------------------------------------------------#
if __name__ == '__main__':
    print('A script for exporting modem performance to an external TSDB v%3.1f\n' % __version__)
    config = ReadConfig(iniFilename)
    dbip = GetStrFromConfig(config, 'DB', 'dbip', 'localhost')
    dbport = GetUnsignedFromConfig(config, 'DB', 'dbport', '8086')
    dbusername = GetStrFromConfig(config, 'DB', 'dbusername', 'root')
    dbpassword = GetStrFromConfig(config, 'DB', 'dbpassword', 'root')
    influxDBClient = connectToDB(dbip, dbport, dbusername, dbpassword)

    for platform in config:
        if platform in nonPlatforms:
            continue
        logger.info('Processing %s' % platform)
        ProcessPlatform(config, platform)

