#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'isim'
__version__ = 2.1


from datetime import datetime
import csv
import sys
import ssl
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    from suds.client import Client
    from suds.cache import NoCache
    import suds
except ImportError:
    if sys.version_info[0] < 3:
        print('This script requires suds package, please install it with "pip install suds-jurko"')
        print('You can install pip itself with "apt-get install python-pip" or "yum install python-pip"')
    else:
        print('This script requires suds package, please install it with "pip3 install suds-jurko" or "pip install suds-jurko"')
        print('You can install pip3 itself with "apt-get install python3-pip" or "yum install python-pip"')
    exit(1)

import urllib, urllib3, socket
for sublogger in logging.Logger.manager.loggerDict:
    if 'suds' or 'urllib' in sublogger:
        logging.getLogger(sublogger).setLevel(logging.CRITICAL)

if sys.version_info[0] == 3:
    import http
if sys.version_info[0] < 3:
    ConnectionExceptions = (urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, urllib3.exceptions.ConnectTimeoutError, urllib3.exceptions.ConnectionError, urllib3.exceptions.HTTPError)
elif sys.version_info[1] < 5:
    ConnectionExceptions = (urllib.error.URLError, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, urllib.error.URLError)
else:
    ConnectionExceptions = (http.client.RemoteDisconnected, urllib.error.URLError, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, urllib.error.URLError)

TimeoutExceptions = (socket.timeout, urllib3.exceptions.TimeoutError, TimeoutError)

class SudsException(Exception):
    pass

try:
    type(unicode)
except NameError:
    unicode = str

class Trend(dict):
    def save2csv(self, filename):
        with open(filename, 'a') as fW:
            writer = csv.DictWriter(fW, ['time', 'min', 'avg', 'max'])
            writer.writeheader()
            for key in self:
                writer.writerow({'time': key, 'min': self[key]['min'], 'avg': self[key]['avg'], 'max': self[key]['max']})


class SOAP:
    @classmethod
    def CreateSOAP(cls, ip, password='D!@10g', username='Administrator', timeout=300, host='localhost', app=__name__, version=__version__, PC='?', customlogger = None):
        soap = None
        log = customlogger or logger
        try:
            soap = SOAP(ip, password, username, timeout, host, app, version, PC, log)
            soap.connect()
        except:
            log.exception('SOAP interface was not created with IP %s' % ip)
        else:
            log.debug('An instance of the SOAP class with IP %s was created' % ip)
        return soap
    @classmethod
    def SOAP(cls, ip, password='D!@10g', username='Administrator', timeout=300, host='localhost', app=__name__, version=__version__, PC='?', customlogger = None):
        soap = None
        log = customlogger or logger
        try:
            soap = SOAP(ip, password, username, timeout, host, app, version, PC, log)
            soap.connect()
        except:
            log.exception('SOAP interface was not created with IP %s' % ip)
        else:
            log.debug('An instance of the SOAP class with IP %s was created' % ip)
        return soap
    def __init__(self, ip, password='D!@10g', username='Administrator', timeout=300, host='localhost', app=__name__, version=__version__, PC='?', customlogger=None):
        self._logger = customlogger or logger
        self._ip = ip
        self._password = password
        self._username = username
        self._timeout = timeout
        self._host = host
        self._app = app
        self._version = version
        self._PC = PC
        self.dmaid = []
        self.protocols = []
        self.lastopertime = 0
        self.interface = None
        self._connection = None
        self._lasttrend = None
    def connect(self):
        self._createSOAPConnection()
        if self.interface:
            a = self.interface.__str__()
            methods = [b.strip() for b in a[a.find(':\n', a.find('Methods ('))+2 : a.find('Types (')].split('\n') if b.strip()]
            for method in methods:
                methodName = method[:method.find('(')]
                if 'GetElements' in method:
                    setattr(self, methodName, self._getSpecialValuesBuilder(method, 'DMAElement'))
                elif 'GetTable' in method:
                    setattr(self, methodName, self._getSpecialValuesBuilder(method, 'DMAParameterTableRow'))
                elif 'TrendData' in method:
                    setattr(self, methodName, self._trendMethodBuilder(method))
                elif '(xs:string connection' in method:
                    setattr(self, methodName, self._methodWithConnectionBuilder(method))
                else:
                    setattr(self, methodName, self._simpleMethodBuilder(method))
            DMAs = self.GetDataMinerAgentsInfo()
            if DMAs and 'DMAInfo' in DMAs:
                self.dmaid = [DMA.ID for DMA in DMAs.DMAInfo]
    def getprotocols(self):
        protocols = self.GetProtocolsForView(-1, True)
        if protocols and 'DMAGenericProperty' in protocols:
            self.protocols = [str(protocol.Key) for protocol in protocols.DMAGenericProperty]
    def debug(self, on=True):
        handler = logging.StreamHandler(sys.stderr)
        l = logging.getLogger('suds.transport.http')
        loggingLevel = logging.INFO
        if on:
            loggingLevel = logging.DEBUG
        handler.setLevel(loggingLevel)
        l.setLevel(loggingLevel)
        l.addHandler(handler)
    def __str__(self):
        return 'soap(%s)' % self._ip
    def __getattr__(self, item):
        self._logger.debug('SOAP method %s was called but not found' % item)
        def func(*args, **kwargs):
            return None
        return func
    def _getSpecialValuesBuilder(self, method, values):
        _methodWithConnection = self._methodWithConnectionBuilder(method, '\nThis method is modified, it returns %s list' % values)
        def _method(*args):
            result = _methodWithConnection(*args)
            if result:
                if values in result:
                    result = result[values]
            else:
                result = list()
            return result
        _method.__doc__ = _methodWithConnection.__doc__
        _method.__name__ = _methodWithConnection.__name__
        return _method
    def _trendMethodBuilder(self, method):
        _methodWithConnection = self._methodWithConnectionBuilder(method, ',\nwhere TrendingSpanType is one of LastHour or LastDay or LastWeek or LastMonth or LastYear')
        def _method(*args, includeSeconds=False, divider=1):
            trend = _methodWithConnection(*args)
            self._lasttrend = trend
            result = Trend()
            if trend:
                if 'FailReason' in trend:
                    if len(args) == 4:
                        element = str(args[0])
                        param = str(args[1])
                        index = str(args[2])
                        period = str(args[3])
                    elif len(args) > 4:
                        element = str(args[0]) + '/' + str(args[1])
                        param = str(args[2])
                        index = str(args[3])
                        period = str(args[4])
                    else:
                        element = 'n/a'
                        param = 'n/a'
                        index = None
                        period = 'n/a'
                    if trend.FailReason == 'No Trend Data Available':
                        self._logger.warning('Trend values for ' + element + ' for parameter ' + param + ((' [' + str(index) + ']') if index else '') + ' are not available for ' + period)
                    else:
                        self._logger.warning('Failed in fetching values for ' + element + ' for parameter ' + param + ((' [' + str(index) + ']') if index else '') + ' for ' + period)
                else:
                    for i in range(0,len(trend.Data.double)):
                        datetimestamp = trend.Timestamps.dateTime[i].strftime('%Y-%m-%d %T')
                        if trend.Status.int[i] == -1000 or trend.Status.int[i] == -4:
                            if trend.Timestamps.dateTime[i].second == 0:
                                self._logger.debug('There is a gap in trending at ' + datetimestamp)
                        elif (includeSeconds or trend.Timestamps.dateTime[i].second == 0) and datetimestamp not in result:
                            result[datetimestamp] = {'min':trend.Min.double[i] / divider, 'avg':trend.Avg.double[i] / divider, 'max': trend.Max.double[i] / divider, 'data': trend.Data.double[i] / divider}
            else:
                if len(args) == 4:
                    element = str(args[0])
                    param = str(args[1])
                    index = str(args[2])
                    period = str(args[3])
                elif len(args) > 4:
                    element = str(args[0]) + '/' + str(args[1])
                    param = str(args[2])
                    index = str(args[3])
                    period = str(args[4])
                else:
                    element = 'n/a'
                    param = 'n/a'
                    index = None
                    period = 'n/a'
                self._logger.warning('Failed in fetching trending values for ' + element + ' for parameter ' + param + ((' [' + str(index) + ']') if index else '') + ' for ' + period)
            return result
        _method.__doc__ = _methodWithConnection.__doc__
        _method.__name__ = _methodWithConnection.__name__
        return _method
    def _methodWithConnectionBuilder(self, method, desc=''):
        _methodSoap = self._methodBuilder(method, self._soapCall, desc)
        expectedArgs = _methodSoap.__closure__[0].cell_contents
        def _method(*args):
            if self.dmaid and len(self.dmaid) == 1 and len(args) + 1 == len(expectedArgs) and 'dmaid' in expectedArgs[0].lower():
                args = (self.dmaid,) + args
            return _methodSoap(*args)
        _method.__doc__ = _methodSoap.__doc__
        _method.__name__ = _methodSoap.__name__
        return _method
    def _simpleMethodBuilder(self, method):
        return self._methodBuilder(method, self._soapBasicFunction)
    def _methodBuilder(self, method, func, desc=''):
        methodName = method[:method.find('(')]
        methodDesc = self._removeXS(method)
        expectedArgs = [a.strip() for a in methodDesc[methodDesc.index('(') + 1 : methodDesc.index(')')].split(',') if a.strip()]
        def _method(*args):
            if len(args) != len(expectedArgs):
                print('Error in arguments, expected: ' + ', '.join(expectedArgs))
                return None
            return func(methodName, *args)
        _method.__doc__ = methodDesc + desc
        _method.__name__ = methodName
        return _method
    def _removeXS(self, method):
        methodDesc = method.replace('xs:', '')
        if 'string connection, ' in methodDesc:
            methodDesc = methodDesc.replace('string connection, ', '')
        elif 'string connection' in methodDesc:
            methodDesc = methodDesc.replace('string connection', '')
        return methodDesc
    def EnableSudsLogging(self):
        for sublogger in logging.Logger.manager.loggerDict:
            if 'suds' in sublogger:
                logging.getLogger(sublogger).setLevel(logging.DEBUG)
    def EnableUrllibLogging(self):
        for sublogger in logging.Logger.manager.loggerDict:
            if 'urllib' in sublogger:
                logging.getLogger(sublogger).setLevel(logging.DEBUG)
    def GetTableForDMAElement(self, DMAElement, paramId, includeCells=True):
        if DMAElement['IsTimeout']:
            self._logger.error(DMAElement['Name'] + ' is in timeout')
        return self.GetTableForParameter(DMAElement.DataMinerID, DMAElement.ID, paramId, includeCells)
    def GetParameterForDMAElement(self, DMAElement, paramId, index=None):
        if DMAElement['IsTimeout']:
            self._logger.error(DMAElement['Name'] + ' is in timeout')
        return self.GetParameter(DMAElement.DataMinerID, DMAElement.ID, paramId, index)
    def GetTrendDataForDMAElement(self, DMAElement, paramId, index, period, includeSeconds=False, divider=1):
        if DMAElement['IsTimeout']:
            self._logger.error(DMAElement['Name'] + ' is in timeout')
        return self.GetTrendDataForParameter(DMAElement.DataMinerID, DMAElement.ID, paramId, index, period, includeSeconds=includeSeconds, divider=divider)
    def _isTimeout(self, inst):
        if 'timeout' in str(type(inst)).lower() or ('args' in inst.__dir__() and len(inst.args) > 0 and ('timeout' in str(inst.args[0]).lower() or 'timed out' in str(inst.args[0]).lower())):
            return True
        return False
    def _createInterface(self):
        url = 'http://%s/API/V1/soap.asmx?wsdl' % self._ip
        try:
            self._logger.debug('Creating SOAP interface with ' + url)
            self.interface = Client(url, username=self._username, password=self._password, timeout=self._timeout, cache=NoCache())
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            self.interface = None
            if self._isTimeout(e):
                self._logger.critical('There was a timeout in creating SOAP interface with %s' % url)
                raise TimeoutError
            elif 'Connection refused' in str(e.args[0]):
                self._logger.critical('SOAP connection refused with %s' % url)
            else:
                self._logger.exception('There was an exception in creating SOAP interface with %s' % url)
        return self.interface
    def _soapBasicFunction(self, func, *args):
        result = None
        start = datetime.now()
        try:
            if not self.interface:
                self._createInterface()
            if self.interface:
                self._logger.debug('Processing SOAP function %s%s' % (func, str(args)))
                result = getattr(self.interface.service, func)(*args)
        except KeyboardInterrupt:
            exit(1)
        except suds.WebFault as e:
            if "Unable to authenticate" in e.fault.faultstring:
                self._logger.error('Authentication error')
            elif "Agent is currently switching" in e.fault.faultstring:
                self._logger.error('DataMiner Agent is currently switching')
            else:
                self._logger.error('There was a SUDS exception: %s' % e.fault.faultstring)
            raise SudsException(e.fault.faultstring)
        except Exception as e:
            self.interface = None
            if self._isTimeout(e):
                self._logger.error('There was a timeout in SOAP method %s' % func)
                raise TimeoutError
            else:
                self._logger.exception('There was an exception in SOAP method %s' % func)
        finally:
            self.lastopertime = datetime.now() - start
        return result
    def _createSOAPConnection(self):
        try:
            self._connection = self._soapBasicFunction('ConnectApp', self._host, self._username, self._password, self._app, self._version, self._PC)
        except:
            self._connection = None
        if self._connection:
            self._logger.debug('SOAP connection with ' + self._ip + ' was established')
        return self._connection
    def _soapCall(self, func, *args):
        result = None
        try:
            if not self.interface:
                self._createSOAPConnection()
            result = self._soapBasicFunction(func, self._connection, *args)
        except SudsException as e:
            if "There's no connection." in e.args[0]:
                self._createSOAPConnection()
                result = self._soapBasicFunction(func, self._connection, *args)
            elif 'No such parameter' in e.args[0]:
                raise SudsException('No such parameter')
            else:
                raise e
        return result

if __name__=='__main__':
    from sys import argv
    if len(argv) > 1: 
        ip = argv[1]
    else:
        ip = ""
    if len(argv) > 2: 
        password = argv[2]
    else:
        password = ""
    if len(argv) > 3: 
        username = argv[3]
    else:
        username = ""
    if ip != "":
        if password != "":
            if username != "":
                soap = SOAP.SOAP(ip, password, username)
            else:
                soap = SOAP.SOAP(ip, password)
        else:
            soap = SOAP.SOAP(ip)
            soap.connect()
        print("\nAn object 'soap' was created, please check it's members for using SOAP interface")

