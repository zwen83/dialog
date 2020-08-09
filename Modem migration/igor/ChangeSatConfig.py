#!/usr/bin/env python3
# -*- coding: utf-8 -*-
''' Change satellite configuration script.
Ths script should be configured using the .ini file.

The script reads all the modems of the chosen Satnet from CMS and creates a list "allmodems".
If the "input file" is defined in the .ini file, it reads the list of modems from that file
and if there are matches with "allmodems", such modems will go to the next stage,
if the file is not defined or there is error reading it, all modems go to the next stage.

If the "exclude file" is defined in the .ini file, the script will exclude those modems from the list of the previous stage

The final list goes to the main cycle where the Satellite configuration is changed directly on every modem of the list.

If configured a reboot could be performed.
If configured an immediate check could be performed.
In case if there was reboot, the immediate check will be done after reboot. Be carefull that in this case the modem should come online to pass the check
The pauseAfterReboot in the .ini file should be configured from the experience of your platform.

After the main cycle exits another cycle could start to check diagnostics report of the modem if changes are accepted.
This is another way of check not the same which could occur before.

If onlyCheckDiagReports is True, then the main cycle will not run.

Files rest.py (or rest.pyc) and ChangeSatConfigSingleModem.py (or .pyc) are used as external modules. These files need to be placed in the same directory.
'''

defaultIniFileName = 'change_sat_config.ini'
loggingFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
dateFormat = '%d/%m/%Y %H:%M:%S'

__author__ = 'isim'
__version__ = 3.1

from time import sleep
import csv
import sys
import logging

formatter = logging.Formatter(loggingFormat, datefmt=dateFormat)
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)

try:
    import configparser
except ImportError:
    print('This script uses "configparser" as an external module. Please install it prior to usage.')
    print('You can install it as a root user: "pip3 install configparser" or "pip install configparser"')
    exit(1)

try:
    import rest as REST
except ImportError:
    print(
        'The module REST is used as an external module. The file rest.py or rest.pyc needs to be placed in the same directory.')
    exit(1)
if REST.__version__ < 2.2:
    print('The file rest.py should be v2.2 or higher')
    exit(1)

try:
    from ChangeSatConfigSingleModem import ProcessSingleModem
except ImportError:
    print('''The module ChangeSatConfigSingleModem is used as an external module.
The file ChangeSatConfigSingleModem.py or ChangeSatConfigSingleModem.pyc needs to be placed in the same directory.''')
    exit(1)


# --------------------------------------------------------------------------#
# ------ Procedure for getting credentials ---------------------------------#
# --------------------------------------------------------------------------#
def GetCredentials(config):
    try:
        ip = config['Access']['cmsip']
        username = config['Access']['username']
        password = config['Access']['password']
    except KeyError:
        print(
            'Non-empty values of cmsip, username and password should be presented in the "Access" section of the .ini file')
        exit(1)
    return ip, username, password


# --------------------------------------------------------------------------#
# ------ Procedure for reading config from an .ini file --------------------#
# --------------------------------------------------------------------------#
def ReadConfig():
    global formatter
    try:
        configuration = configparser.ConfigParser()

        configuration.optionxform = lambda option: option
        try:
            print(sys.argv)  # ['C:/Users/zwen.073111-PC/dialog/Modem migration/igor/ChangeSatConfig.py']

            if len(sys.argv) > 1:
                print(sys.argv)
                iniFileName = sys.argv[1]
            else:
                iniFileName = defaultIniFileName
            res = configuration.read(iniFileName)
            # print(res)
            # print(len(configuration))
        except (configparser.DuplicateOptionError, configparser.ParsingError) as Err:
            print('ERROR:', Err)
            exit(1)
        if len(configuration) < 2:
            print('%s file not found' % iniFileName)
            exit(1)
        # check for obligitary settings in the .ini file
        config = dict()
        for section in configuration:
            config[section] = dict()
            print(config)
            '''
            {'DEFAULT': {}, 
            'Access': {'cmsip': '192.168.80.45', 'username': 'hno', 'password': 'D!@10g'}, 
            'Satnet': {'SatnetName': 'SN1', 'alternativeFrequency': '12875000000', 'alternativeSymbolRate': '30000000', 'alternativePolarization': 'V', 'enableAlternativeCarrier': 'true'}, 
            'Files': {'inputFilename': 'modems.csv', 'excludeFilename': 'processed_modems.csv', 'outputFilename': 'processed_modems.csv'}, 
            'Logging': {'loggingLevel': 'info', 'logfile': 'change_sat_config.log'}, 
            'Rebooting': {'pauseBeforeReboot': '1', 'reboot': 'false', 'pauseAfterReboot': '80'}, 
            'Other': {}}

            
            '''
            print(configuration[section])  #<Section: Other>
            for key in configuration[section]:
                config[section][key] = configuration[section][key]  #将configuration读出来的配置写入config里
                # print(config)
                '''
                {
                'DEFAULT': {}, 
                'Access': {'cmsip': '192.168.80.45', 'username': 'hno', 'password': 'D!@10g'}, 
                'Satnet': {'SatnetName': 'SN1', 'alternativeFrequency': '12875000000', 'alternativeSymbolRate': '30000000', 'alternativePolarization': 'V', 'enableAlternativeCarrier': 'true'}, 
                'Files': {'inputFilename': 'modems.csv', 'excludeFilename': 'processed_modems.csv', 'outputFilename': 'processed_modems.csv'},
                'Logging': {'loggingLevel': 'info', 'logfile': 'change_sat_config.log'}, 
                'Rebooting': {'pauseBeforeReboot': '1', 'reboot': 'false', 'pauseAfterReboot': '80'}, 
                'Other': {'checkAfterChange': 'false', 'checkDiagReportsAfterProcessing': 'true', 'onlyCheckDiagReports': 'false', 'cyclePause': '1'}
                 }
                '''
        for key in ['Access', 'Satnet']:
            if key not in config:
                print('No %s section found in the .ini file' % key)
                exit(1)
        # check if Frequency and Symbol Rate  is defined correctly
        a = CorrectFreqAndSymb(config, 'alternativeFrequency')
        b = CorrectFreqAndSymb(config, 'mainFrequency')
        c = CorrectFreqAndSymb(config, 'alternativeSymbolRate')
        d = CorrectFreqAndSymb(config, 'mainSymbolRate')

        if a > 100000000000 or (a < 900000000 and a != 0) or b > 100000000000 or (b < 900000000 and b != 0):
            print('Frequency is not defined correctly in the .ini file')
            exit(1)
        if c > 1000000000 or d > 1000000000:
            print('Symbol Rate is not defined correctly in the .ini file')
            exit(1)
        # check if Polarization is defined correctly
        CorrectPol(config, 'mainPolarization')
        CorrectPol(config, 'alternativePolarization')
        # check if TS Mode is defined correctly
        CorrectTSMode(config, 'mainTSMode')
        CorrectTSMode(config, 'alternativeTSMode')
        # check if TimeSliceNumber is defined correctly
        CorrectTimeSliceNumber(config, 'mainTimeSliceNumber')
        CorrectTimeSliceNumber(config, 'alternativeTimeSliceNumber')

        if 'enMainCarrier' in config['Satnet']:
            config['Satnet']['enableMainCarrier'] = GetBooleanFromConfig(config, 'Satnet', 'enMainCarrier')
        else:
            config['Satnet']['enableMainCarrier'] = True

        if 'enableAlternativeCarrier' in config['Satnet']:
            config['Satnet']['enableAlternativeCarrier'] = GetBooleanFromConfig(config, 'Satnet',
                                                                                'enableAlternativeCarrier')
        elif config['Satnet']['alternativeFrequency'] or config['Satnet']['alternativeSymbolRate'] or config['Satnet'][
            'alternativeTSMode'] or config['Satnet']['alternativePolarization'] != -1:
            config['Satnet']['enableAlternativeCarrier'] = True
        else:
            config['Satnet']['enableAlternativeCarrier'] = 'NoChange'

        config['reboot'] = GetBooleanFromConfig(config, 'Rebooting', 'reboot')
        config['checkAfterChange'] = GetBooleanFromConfig(config, 'Other', 'checkAfterChange')
        config['checkDiagReportsAfterProcessing'] = GetBooleanFromConfig(config, 'Other',
                                                                         'checkDiagReportsAfterProcessing')
        config['copyMainCarrierToMainPointingCarrier'] = GetBooleanFromConfig(config, 'Satnet',
                                                                              'copyMainCarrierToMainPointingCarrier')
        config['copyAltCarrierToAltPointingCarrier'] = GetBooleanFromConfig(config, 'Satnet',
                                                                            'copyAltCarrierToAltPointingCarrier')
        config['onlyCheckDiagReports'] = GetBooleanFromConfig(config, 'Other', 'onlyCheckDiagReports')
        config['pauseAfterChange'] = GetIntFromConfig(config, 'Other', 'pauseAfterChange')
        config['Rebooting']['pauseAfterReboot'] = GetIntFromConfig(config, 'Rebooting', 'pauseAfterReboot')

        if (config['Satnet']['mainFrequency'] or config['Satnet']['mainSymbolRate'] or config['Satnet']['mainTSMode'] or
            config['Satnet']['mainPolarization'] != -1) and not (
                config['checkAfterChange'] or config['checkDiagReportsAfterProcessing'] or config[
            'onlyCheckDiagReports']):
            print(
                'You are going to change one or several parameters of the main carrier but you have not configured any check. That is too dangerous.')
            exit(1)

        # configure logging of the script
        if 'Logging' in config:
            if 'logfile' in config['Logging'] and config['Logging']['logfile']:
                fH = logging.FileHandler(config['Logging']['logfile'])
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
            logger.debug('**** ChangeSatConfig v.%3.1f. Start of log ****', __version__)
            if loglevel == 'FULLDEBUG':
                logging.getLogger('SingleModem').setLevel(logging.DEBUG)
            if loglevel == 'FULLDEBUGWITHREST':
                logging.getLogger('rest').setLevel(logging.DEBUG)
    except OSError:
        print('Reading config file failed')
        exit(1)
    logger.debug('Config file has been read')
    return config


def CorrectPol(config, key):
    try:
        pol = config['Satnet'][key]
    except KeyError:
        config['Satnet'][key] = -1
    else:
        a = GetPolNumber(pol)
        if a == -1:
            print(
                'ERROR: Polarization should be one symbol out of "H", "V", "L" or "R" in the "Satnet" section of the .ini file, but you have: %s' % pol)
            exit(1)
        else:
            config['Satnet'][key] = a


def GetPolNumber(polarization):
    pol = polarization.upper()
    if pol == 'H' or pol == 'POLARIZATION_LINEAR_HORIZONTAL':
        result = 0
    elif pol == 'V' or pol == 'POLARIZATION_LINEAR_VERTICAL':
        result = 1
    elif pol == 'L' or pol == 'POLARIZATION_CIRCULAR_LEFT':
        result = 2
    elif pol == 'R' or pol == 'POLARIZATION_CIRCULAR_RIGHT':
        result = 3
    else:
        result = -1
    return result


def GetPolLetter(pol):
    if pol == 0:
        result = 'H'
    elif pol == 1:
        result = 'V'
    elif pol == 2:
        result = 'L'
    elif pol == 3:
        result = 'R'
    else:
        result = ''
    return result


def CorrectTSMode(config, key):
    try:
        TSMode = config['Satnet'][key].upper()
    except KeyError:
        config['Satnet'][key] = ''
    else:
        if TSMode == 'DVB-S':
            config['Satnet'][key] = 'dvbs'
        elif TSMode == 'DVB-S2 CCM':
            config['Satnet'][key] = 'dvbs2_ccm'
        elif TSMode == 'DVB-S2 ACM':
            config['Satnet'][key] = 'dvbs2_acm'
        elif TSMode == 'DVB-S2X':
            config['Satnet'][key] = 'dvbs2x'
        elif TSMode == 'DVB-S2X TIMESLICED':
            config['Satnet'][key] = 'dvbs2x_timesliced'
        else:
            print(
                'Transport Stream Mode should be one of "DVB-S", "DVB-S2 CCM", "DVB-S2 ACM", "DVB-S2X", "DVB-S2X Timesliced" in the "Satnet" section of the .ini file')
            exit(1)


def CorrectTimeSliceNumber(config, key):
    try:
        config['Satnet'][key] = int(config['Satnet'][key])
    except ValueError:
        print('%s should be an integer number between 1 and 62 defined in the "Satnet" section of the .ini file' % key)
        exit(1)
    except KeyError:
        config['Satnet'][key] = 0
    else:
        if config['Satnet'][key] < 1 or config['Satnet'][key] > 62:
            print(
                '%s should be an integer number between 1 and 62 defined in the "Satnet" section of the .ini file' % key)
            exit(1)


def CorrectFreqAndSymb(config, key):
    try:
        config['Satnet'][key] = int(config['Satnet'][key])
    except ValueError:
        print('%s should be a positive integer number defined in the "Satnet" section of the .ini file' % key)
        exit(1)
    except KeyError:
        config['Satnet'][key] = 0
    else:
        if config['Satnet'][key] < 100000:
            print('%s should be an integer number > 100000 defined in the "Satnet" section of the .ini file' % key)
            exit(1)
    return config['Satnet'][key]


def GetBooleanFromConfig(config, section, key):
    try:
        if config[section][key].lower() == 'true' or config[section][key].lower() == 'yes':
            result = True
        elif config[section][key].lower() == 'false' or config[section][key].lower() == 'no':
            result = False
        else:
            print('The value %s should be true/false or yes/no' % key)
            exit(1)
    except KeyError:
        result = False
    return result


def GetIntFromConfig(config, section, key):
    try:
        result = int(config[section][key])
    except KeyError:
        result = 0
    except ValueError:
        print('%s should be an integer number in the .ini file' % key)
        exit(1)
    return result


# --------------------------------------------------------------------------#
# ------ Procedure for reading all modems from CMS -------------------------#
# --------------------------------------------------------------------------#
def GetAllModems(rest, satnet):
    params = {'satelliteNetworkId': satnet['systemId']}
    params['property'] = ['macAddress', 'remoteGuiUrl']
    params['locked'] = False
    params['start'] = 0
    params['limit'] = 100

    # a cycle for reading 100 modems per request in order not to overload the CMS
    modems = list()
    bGetMore = True
    while bGetMore:
        logger.info('GET CMS modems from %i to %i' % (params['start'] + 1, params['start'] + params['limit']))
        try:
            modemsPart = rest.GET('modem/collect', params=params)
        except REST.ConnectionError:
            logger.critical('Error connecting to the hub')
            exit(1)
        except REST.AuthorizationError:
            logger.critical('Check credentials in the .ini file')
            exit(1)
        except KeyboardInterrupt:
            print('Keyboard interrupt')
            exit(1)
        if not modemsPart or type(modemsPart) != list:
            logger.warning(
                'GET CMS modems from %i to %i failed' % (params['start'] + 1, params['start'] + params['limit']))
            bGetMore = False
        else:
            # if a correct reply was received add those modems to the list
            logger.debug('Adding retrieved modems to the list')
            for modem in modemsPart:
                if 'remoteGuiUrl' in modem and modem['remoteGuiUrl']:
                    modems.append(modem)
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
            print(satnets)
        exit(1)
    return modems


# --------------------------------------------------------------------------#
# ------ Procedure for reading all Satnets from CMS ------------------------#
# --------------------------------------------------------------------------#
def GetSatnets(rest):
    try:
        satnets = rest.GET('satellite-network/collect', params={'property': 'id'})
    except:
        logger.exception('Failed while getting Satnets from CMS')
        exit(1)
    return satnets


# --------------------------------------------------------------------------#
# ------ Procedure for inclduding or excluding modems to/from --------------#
# ------ the to-process list -----------------------------------------------#
# --------------------------------------------------------------------------#
def IncludeExcludeModems(modems, filename, action):
    if not (modems and type(modems) == list and len(modems) > 0):
        logger.error('No modems to process')
        exit(1)
    # convert a modem list to a dict for better performance
    modemsDict = dict()
    for modem in modems:
        modemsDict[modem['macAddress']] = modem
    logger.debug('Reading modems from the file %s' % filename)
    modemsToProcess = list()
    try:
        fR = open(filename)
        reader = csv.DictReader(fR)
        if not reader.fieldnames or 'MacAddress' not in reader.fieldnames:
            logger.warning(
                'A csv file %s should contain a column with "MacAddress" header. All modems will be processed.' % filename)
            return modems
        for row in reader:
            if row['MacAddress'] in modemsDict:
                if action == 'exclude':
                    logger.debug('Removing MacAddress %s from the to-process list' % row['MacAddress'])
                    modemsDict.pop(row['MacAddress'])
                else:
                    modemsToProcess.append(modemsDict[row['MacAddress']])
                    logger.debug('Modem with MacAddress %s was added to the to-process list' % row['MacAddress'])
        fR.close()
    except (OSError, IOError):
        logger.error('Error reading modems from the file %s. All modems will be processed.' % filename)
        modemsToProcess = modems
    # convert the modems dict back to a list
    else:
        if action == 'exclude':
            for key in modemsDict:
                modemsToProcess.append(modemsDict[key])
    return modemsToProcess


# --------------------------------------------------------------------------#
# ------ Procedure that takes out modems one by one from a given list ------#
# ------ and pass it to the procedure ProcessSingleModem(...) --------------#
# --------------------------------------------------------------------------#
def ProcessAndWriteModems(modemsToProcess, rest, config):
    print(modemsToProcess)
    if not (modemsToProcess and type(modemsToProcess) == list and len(modemsToProcess) > 0):
        logger.warning('No modems to process')
        exit(1)
    logger.warning('The number of modems to process: %i', len(modemsToProcess))
    writer = None
    # try to open a file to write the processed modems
    try:
        logger.debug('Opening file %s for writing (append)' % config['Files']['outputFilename'])
    except KeyError:
        logger.warning('Output file is not defined')
    else:
        try:
            fW = open(config['Files']['outputFilename'], 'a')
            writer = csv.DictWriter(fW, ['MacAddress'])
            if fW.tell() == 0:
                writer.writeheader()
        except OSError:
            logger.error('Error opening processed modems file %s' % config['Files']['outputFilename'])
            writer = ''

    # define variables for ProcessSingleModem(...)
    mainCarrier = {
        'Freq': config['Satnet']['mainFrequency'],
        'SymbolRate': config['Satnet']['mainSymbolRate'],
        'Polarization': config['Satnet']['mainPolarization'],
        'TSMode': config['Satnet']['mainTSMode'],
        'TimeSliceNumber': config['Satnet']['mainTimeSliceNumber'],
        'Enabled': config['Satnet']['enableMainCarrier'],
        'copyToPointingCarrier': config['copyMainCarrierToMainPointingCarrier']}

    altCarrier = {
        'Freq': config['Satnet']['alternativeFrequency'],
        'SymbolRate': config['Satnet']['alternativeSymbolRate'],
        'Polarization': config['Satnet']['alternativePolarization'],
        'TSMode': config['Satnet']['alternativeTSMode'],
        'TimeSliceNumber': config['Satnet']['alternativeTimeSliceNumber'],
        'Enabled': config['Satnet']['enableAlternativeCarrier'],
        'copyToPointingCarrier': config['copyAltCarrierToAltPointingCarrier']}

    # the main cycle
    modemsPreProcessed = list()
    modemsProcessed = list()
    try:
        for modem in modemsToProcess:
            logger.info('Processing modem %s' % modem['macAddress'])
            url = modem['remoteGuiUrl']
            if config['onlyCheckDiagReports']:
                logger.info('Checking modem %s parameters with diagnostics report' % modem['macAddress'])
                reply = CheckDiagReport(rest, url, mainCarrier, altCarrier)
            else:
                try:
                    reply = ProcessSingleModem(rest, url, mainCarrier, altCarrier, config['checkAfterChange'],
                                               config['reboot'], config['pauseAfterChange'],
                                               config['Rebooting']['pauseAfterReboot'])
                except:
                    logger.exception('Exception in SingleModem module')
                    reply = False
                if reply and config['checkAfterChange']:
                    if type(reply) == tuple and len(reply) == 2:
                        mainCarrierReceived, altCarrierReceived = reply
                        reply = CheckIdentity(mainCarrier, mainCarrierReceived, 'Main') and CheckIdentity(altCarrier,
                                                                                                          altCarrierReceived,
                                                                                                          'Alternative')
                    else:
                        reply = False
                    if not reply:
                        logger.error("Modem %s didn't pass the check with the diagnostics report" % modem['macAddress'])
            if reply:
                modemsPreProcessed.append(modem)
                if config['reboot'] and not config['checkAfterChange']:
                    logger.info('Modem %s was processed and rebooted' % modem['macAddress'])
                else:
                    if config['onlyCheckDiagReports']:
                        logger.info('Modem %s is ok' % modem['macAddress'])
                    else:
                        logger.info('Modem %s was successfully processed' % modem['macAddress'])
                    if writer and (config['onlyCheckDiagReports'] or not config['checkDiagReportsAfterProcessing']):
                        logger.info('Appending modem %s to the processed modems file' % modem['macAddress'])
                        writer.writerow({'MacAddress': modem['macAddress']})
            else:
                logger.warning('Modem %s was not processed' % modem['macAddress'])
            # make a pause if configured
            try:
                pause = int(config['Other']['cyclePause'])
                if pause:
                    logger.debug('Pause for %i seconds' % pause)
                    sleep(pause)
            except KeyError:
                pass
            print('Process progress: %4.2f' % ((modemsToProcess.index(modem) + 1) / len(modemsToProcess) * 100) + '%')
        if config['checkDiagReportsAfterProcessing'] and not config['onlyCheckDiagReports'] and len(
                modemsPreProcessed) > 0:
            logger.info('All modems processed, we are going to check them now with diagnosts reports')
            for modem in modemsPreProcessed:
                logger.info('Checking modem %s parameters with diagnostics report' % modem['macAddress'])
                if CheckDiagReport(rest, modem['remoteGuiUrl'], mainCarrier, altCarrier):
                    modemsProcessed.append(modem)
                    logger.info('Modem %s was successfully checked' % modem['macAddress'])
                    if writer:
                        logger.info('Appending modem %s to the processed modems file' % modem['macAddress'])
                        writer.writerow({'MacAddress': modem['macAddress']})
                else:
                    logger.error("Modem %s didn't pass the check with the diagnostics report" % modem['macAddress'])
                print('Diag report checking progress: %4.2f' % (
                            (modemsPreProcessed.index(modem) + 1) / len(modemsPreProcessed) * 100) + '%')
        else:
            modemsProcessed = modemsPreProcessed
    except OSError:
        logger.error('Error writing processed modem to the file %s' % config['Files']['outputFilename'])
    except KeyError:
        logger.critical('An error in the CMS respond while processing')
        exit(1)
    except KeyboardInterrupt:
        print('Keyboard interrupt')
        exit(1)
    finally:
        if writer: fW.close()
    modemsNotProcessed = list()
    for modem in modemsToProcess:
        if modem not in modemsProcessed:
            modemsNotProcessed.append(modem)
    return modemsNotProcessed


# --------------------------------------------------------------------------#
# ------ Procedure that checks a modem if it has the needed parameters -----#
# --------------------------------------------------------------------------#
def CheckDiagReport(rest, url, mainCarrier, altCarrier):
    result = False
    try:
        logger.debug('Requesting the diagnostics report')
        diag = rest.GET('cgi-bin/gui_diagnostic_report', '', url)
        if not diag:
            logger.debug("The diagnostics wasn't received")
            return False
        chunk = diag[diag.index('forward_link.dvb_s2_mode'):]
        data = chunk[chunk.index(':'):]
        pre = data[1:data.index('\n')].strip()
        mainTSMode = 'dvbs' if pre == 0 else 'dvbs2_ccm' if pre == 1 else 'dvbs2_acm' if pre == 2 else ''

        chunk = diag[diag.index('forward_link.frequency'):]
        data = chunk[chunk.index(':'):]
        pre = data[1:data.index('\n')].strip()
        mainFrequency = int(pre[:pre.index('*')].strip()) * 100

        chunk = diag[diag.index('forward_link.polarization'):]
        data = chunk[chunk.index(':'):]
        pre = data[1:data.index('\n')].strip()
        mainPolarization = GetPolNumber(pre)

        chunk = diag[diag.index('forward_link.symbol_rate'):]
        data = chunk[chunk.index(':'):]
        pre = data[1:data.index('\n')].strip()
        mainSymbolRate = int(pre[:pre.index('*')].strip()) * 100

        if 'forward_link.valid' in diag:
            chunk = diag[diag.index('forward_link.valid'):]
            data = chunk[chunk.index(':'):]
            pre = data[1:data.index('\n')].strip()
            mainEnabled = True if pre == 'yes' else False
        else:
            mainEnabled = 'NoChange'

        chunk = diag[diag.index('forward_link2.dvb_s2_mode'):]
        data = chunk[chunk.index(':'):]
        pre = data[1:data.index('\n')].strip()
        altTSMode = 'dvbs' if pre == 0 else 'dvbs2_ccm' if pre == 1 else 'dvbs2_acm' if pre == 2 else ''

        chunk = diag[diag.index('forward_link2.frequency'):]
        data = chunk[chunk.index(':'):]
        pre = data[1:data.index('\n')].strip()
        altFrequency = int(pre[:pre.index('*')].strip()) * 100

        chunk = diag[diag.index('forward_link2.polarization'):]
        data = chunk[chunk.index(':'):]
        pre = data[1:data.index('\n')].strip()
        altPolarization = GetPolNumber(pre)

        chunk = diag[diag.index('forward_link2.symbol_rate'):]
        data = chunk[chunk.index(':'):]
        pre = data[1:data.index('\n')].strip()
        altSymbolRate = int(pre[:pre.index('*')].strip()) * 100

        if 'forward_link2.valid' in diag:
            chunk = diag[diag.index('forward_link2.valid'):]
            data = chunk[chunk.index(':'):]
            pre = data[1:data.index('\n')].strip()
            altEnabled = True if pre == 'yes' else False
        else:
            altEnabled = 'NoChange'

        mainCarrierReceived = {'Freq': mainFrequency, 'SymbolRate': mainSymbolRate, 'Polarization': mainPolarization,
                               'TSMode': mainTSMode, 'Enabled': mainEnabled}
        altCarrierReceived = {'Freq': altFrequency, 'SymbolRate': altSymbolRate, 'Polarization': altPolarization,
                              'TSMode': altTSMode, 'Enabled': altEnabled}

        result = CheckIdentity(mainCarrier, mainCarrierReceived, 'Main') and CheckIdentity(altCarrier,
                                                                                           altCarrierReceived,
                                                                                           'Alternative')
    #    except (KeyError, AttributeError, ValueError, REST.ConnectionError) as Err:
    except REST.ConnectionError as Err:
        logger.debug(Err)
        result = False
    return result


def CheckIdentity(carrierData, carrierDataReceived, word):
    result = True
    if (carrierData['Enabled'] and carrierDataReceived['Enabled']) or carrierData['Enabled'] == 'NoChange' or \
            carrierDataReceived['Enabled'] == 'NoChange':
        if carrierData['Freq'] and carrierData['Freq'] != carrierDataReceived['Freq']:
            logger.debug('Check failed: received %s Frequency is %i while expected is %i', word,
                         carrierDataReceived['Freq'], carrierData['Freq'])
            result = False
        if carrierData['SymbolRate'] and carrierData['SymbolRate'] != carrierDataReceived['SymbolRate']:
            logger.debug('Check failed: received %s SymbolRate is %i while expected is %i', word,
                         carrierDataReceived['SymbolRate'], carrierData['SymbolRate'])
            result = False
        if carrierData['Polarization'] > -1 and carrierData['Polarization'] != carrierDataReceived['Polarization']:
            logger.debug('Check failed: received %s Polarization is %s while expected is %s', word,
                         GetPolLetter(carrierDataReceived['Polarization']), GetPolLetter(carrierData['Polarization']))
            result = False
        if carrierData['TSMode'] and carrierData['TSMode'] != carrierDataReceived['TSMode']:
            logger.debug('Check failed: received %s TSMode is %s while expected is %s', word,
                         carrierDataReceived['TSMode'], carrierData['TSMode'])
            result = False
    elif carrierData['Enabled'] == carrierDataReceived['Enabled']:
        result = True
    else:
        logger.debug('Check failed: received %s carrier enabled is %s while expected is %s', word,
                     'True' if carrierDataReceived['Enabled'] else 'False',
                     'True' if carrierData['Enabled'] else 'False')
        result = False
    return result


# --------------------------------------------------------------------------#
# ------ Procedure for connecting to a Dialog hub --------------------------#
# --------------------------------------------------------------------------#
def ConnectToDialog(config):
    ip, username, password = GetCredentials(config)
    try:
        rest = REST.REST(ip, username, password)
        if not rest:
            logger.critical('Error during connecting to the hub')
            exit(1)
        satnets = GetSatnets(rest)
        if not satnets or len(satnets) == 0:
            logger.debug('Connection to Dialog failed')
            exit(1)
        logger.debug('Connection to Dialog is ok')
    except:
        print('ERROR: Check the CMS IP configured in the .ini. file')
        exit(1)
    try:
        if 'SatnetName' in config['Satnet']:
            for s in satnets:
                if s['id']['name'] == config['Satnet']['SatnetName']:
                    satnet = s['id']
                    break
        elif 'SatnetId' in config['Satnet']:
            satnetid = GetIntFromConfig(config, 'Satnet', 'SatnetId')
            for s in satnets:
                if s['id']['systemId'] == satnetid:
                    satnet = s['id']
                    break
        else:
            print('The Satnet is configured wrong. There are %i Satnets available:' % len(satnets))
            for satnet in satnets:
                print(satnet['name'])
            exit(1)
    except KeyError:
        if len(satnets) != 1:
            print('The Satnet is configured wrong. There are %i Satnets available:' % len(satnets))
            for satnet in satnets:
                print(satnet['name'])
            exit(1)
        else:
            satnet = satnets[0]
    return rest, satnet


# --------------------------------------------------------------------------#
# ------ The entry point ---------------------------------------------------#
# --------------------------------------------------------------------------#
if __name__ == '__main__':
    print('A script for changing Satellite Configuration directly in modems v%3.1f\n' % __version__)
    config = ReadConfig()
    # print(config)
    '''
    {
    'DEFAULT': {}, 'Access': {'cmsip': '192.168.80.45', 'username': 'hno', 'password': 'D!@10g'}, 
    'Satnet': {'SatnetName': 'SN1', 'alternativeFrequency': 12875000000, 'alternativeSymbolRate': 30000000, 'alternativePolarization': 1, 'enableAlternativeCarrier': True, 'mainFrequency': 0, 'mainSymbolRate': 0, 'mainPolarization': -1, 'mainTSMode': '', 'alternativeTSMode': '', 'mainTimeSliceNumber': 0, 'alternativeTimeSliceNumber': 0, 'enableMainCarrier': True}, 
    'Files': {'inputFilename': 'modems.csv', 'excludeFilename': 'processed_modems.csv', 'outputFilename': 'processed_modems.csv'}, 
    'Logging': {'loggingLevel': 'info', 'logfile': 'change_sat_config.log'}, 
    'Rebooting': {'pauseBeforeReboot': '1', 'reboot': 'false', 'pauseAfterReboot': 80}, 
    'Other': {'checkAfterChange': 'false', 'checkDiagReportsAfterProcessing': 'true', 'onlyCheckDiagReports': 'false', 'cyclePause': '1'}, 
    'reboot': False, 'checkAfterChange': False, 'checkDiagReportsAfterProcessing': True, 'copyMainCarrierToMainPointingCarrier': False, 'copyAltCarrierToAltPointingCarrier': False, 'onlyCheckDiagReports': False, 'pauseAfterChange': 0
    }
    
    '''

    rest, satnet = ConnectToDialog(config)
    allmodems = GetAllModems(rest, satnet)
    if 'Files' in config and 'inputFilename' in config['Files']:
        modems = IncludeExcludeModems(allmodems, config['Files']['inputFilename'], 'include')
    else:
        modems = allmodems
    if 'Files' in config and 'excludeFilename' in config['Files']:
        modemsToProcess = IncludeExcludeModems(modems, config['Files']['excludeFilename'], 'exclude')
    else:
        modemsToProcess = modems
    modemsNotProcessed = ProcessAndWriteModems(modemsToProcess, rest, config)
    try:
        logger.info('**** Done. Number of modems left = %i ****' % len(modemsNotProcessed))
        if not logger.isEnabledFor(logging.INFO):
            print('Done. Number of modems left = %i' % len(modemsNotProcessed))
    except:
        logger.exception('There is a misconfiguration or system fault, no modem were processed')
    if 'Files' in config and 'modemsLeftFilename' in config['Files']:
        fW = open(config['Files']['modemsLeftFilename'], 'wt')
        writer = csv.DictWriter(fW, ['MacAddress'])
        writer.writeheader()
        for modem in modemsNotProcessed:
            writer.writerow({'MacAddress': modem['macAddress']})
        fW.close()