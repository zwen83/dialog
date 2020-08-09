'''rest v3.2
This module provides a class REST for basic functions get, post, put and delete of REST API

While creating an object of the class REST an IP address (and port optionally) to the REST server should be provided
a = rest.REST('192.168.86.7')
a = rest.REST('192.168.86.7:80')

Also credentials could be provided:
a = rest.REST('192.168.86.7', 'user1', 'very_diFFicult_passw0rd')

Alternatively credentials could be set or changed later:
a.credentials('user1', 'very_diFFicult_passw0rd')

Sometimes data type definition that should be returned by server is required, this also should be done while creating an object:
a = rest.REST('192.168.86.7', 'user1', 'very_diFFicult_passw0rd', 'vnd.newtec.conf-v1') or
a = rest.REST('192.168.86.7', contenttype = 'vnd.newtec.conf-v1') if no credentials needed

After creating an object of REST class you can use its functions:
- GET(resource) - sends a GET request via REST to a given resource of the server and returns a result suitable for Python usage

- POST(resource, params) - sends a POST request via REST to a given resource with given parameters and returns a result suitable for Python usage

- PUT(resource, params) - sends a PUT request via REST to a given resource with given parameters and returns a result suitable for Python usage

- DELETE(resource, params = '') - sends a DELETE request via REST to a given resource with given parameters (if needed) and returns a result suitable for Python usage

Example:

import rest

a = rest.REST('192.168.86.7', 'user1', 'very_diFFicult_passw0rd', 'vnd.newtec.conf-v1')

#depending on what server returns "config" could be a list, dictionary, or whatever else
config = a.GET('hub-module')

newconfig = {'var1': 34, 'var2': 5}
newid = a.POST('hub-module/1', newconfig)
#usually POST returns an id of the created object but could be an error message or something else, you should follow server API documentation

changedconfig = {'var2': 100, 'id': newid}
result = a.PUT('hub-module/1', changedconfig)

#at the end you can delete the object. The following example gives you only an idea
a.DELETE('hub-module/1/%i' % int(newid))

There is additional functionality, please contact ISIM from Newtec for futher explanation
'''

__author__  = 'isim'
__version__ = 3.3

#Importing needed modules
#the module "requests" probably needs to be installed on your PC first
try:
    import requests
except ImportError:
    print('Please install a module "requests" before launching this script')
    exit(1)

try:
    import json
except ImportError:
    print('Please install a module "json" before launching this script')
    exit(1)

try:
    type(unicode)
except NameError:
    unicode = str

import logging
logging.getLogger('requests').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class ConnectionError(Exception):
    pass

class AuthorizationError(Exception):
    pass

class DialogError(Exception):
    pass

#class REST is the main class of this module, most functionality is realized here 
class REST:
    '''Class REST realizes REST calls to a server. Access to the server should be passed to a constructor (ip and credentials)
    Example:
    
    import rest
    a = rest.REST('192.168.86.7', 'user1', 'very_diFFicult_passw0rd')
    
    the class provides four procedures that corresponds to the main REST calls: GET, POST, PUT and DELETE
    Implementation is done via universal private procedure "_request" which is not to be used by a user
    '''
    def __init__(self, ip, username = 'hno', password = 'D!@10g', contenttype = '', timeout=300, keepcookies=True):
        '''A constructor of the class REST. It tests its arguments and initializes the class.
        _init__(ip, username, password, contenttype)
        ip is obligitary, the remaining arguments could be omitted 
        
        username and password could be also set later with the function "credentials"
        
        the last argument "contenttype" specifies the data format which server should return back to the user.
        In most cases it could be omitted.
        '''
        if not (isString(ip) and isString(username) and isString(password) and isString(contenttype)):
            raise ValueError('All arguments passed to the constructor should be of a string type')
        if not validIP(ip):
            raise ValueError('IP address provided to the module REST is not valid')
        self._ip = ip
        self._auth = (username, password)
        if contenttype:
            contenttype += '+'
        self._headers = {'Content-Type': 'application/%sjson' % contenttype, 'Accept': 'application/json'}  
        self.reply = requests.models.Response()
        self._timeout = timeout
        self._keepcookies = keepcookies
        self.cookies = None
        logger.debug('An instance of the REST class with ip %s created' % ip)

    def credentials(self, username, password):
        '''A procedure that can change credentials for accessing the server
        '''
        if not (isString(username) and isString(password)):
            logger.error('Credential can not be changed as both username and password must be of a string type')
        else:
            self._auth = (username, password)
            logger.debug('Credential changed')
    
#all magic happens here
    def _request(self, function, resource, payload, service, interface='/rest/', params=None, cookies=None, timeout=0, headers={}):
        '''_request(function, resource, params)
        A private function that executes the needed REST call and returns a result or error message
        '''
        request_url = 'http://' + self._ip + service + interface + resource
        logger.debug('%s to %s %s %s', function.upper(), request_url, (('with %s' % payload) if payload else ''), (('and %s' % params) if params else ''))
        try:
            self.reply = getattr(requests, function)(request_url, auth=self._auth, headers=headers or self._headers, json=payload, params=params, cookies=(cookies if cookies else self.cookies), timeout=(timeout if timeout else self._timeout))
            if self._keepcookies:
                self.cookies = self.reply.cookies
            logger.debug(self.reply.status_code)
            logger.debug(self.reply.reason)
            logger.debug(self.reply.text)
        except OSError as err:
            logger.debug('Cannot reach the host (%s)', err)
            raise ConnectionError
        except KeyboardInterrupt as err:
            logger.debug('Keyboard interrupt while connecting to the host')
            raise KeyboardInterrupt
        if self.reply.reason == 'Authorization Required':
            logger.debug('Authorization Required')
            raise AuthorizationError
        if self.reply.status_code == requests.codes.ok:
            try:
                result = self.reply.json()
            except ValueError:
                result = self.reply.text
        else:
            logger.info('%s to %s failed %s', function.upper(), request_url, (('with %s' % params) if params else ''))
            logger.info('error code = %i, reason = %s', self.reply.status_code, self.reply.reason)
            try:
                error = self.reply.json()
                if isinstance(error, list):
                    for errorMessage in error:
                        if isinstance(errorMessage, dict) and "errorMessage" in errorMessage.keys() and "errorCode" in errorMessage.keys():
                            logger.debug(errorMessage["errorCode"] + ": " + errorMessage["errorMessage"])
                            raise DialogError(errorMessage["errorCode"] + ": " + errorMessage["errorMessage"])
            except ValueError:
                logger.debug('error text: %s' % self.reply.text)
            result = False
        return result
    def __str__(self):
        return 'rest(%s)' % self._ip

#next four functions provide GET, POST, PUT and DELETE
    def GETFILE(self, resource, service = '', params='', cookies=None, timeout=0, headers={}):
        return self._request('get', resource, '', service, '', params, cookies, timeout, headers={'Content-Type': 'text/csv'})
    def GET(self, resource, service = '', interface = '/rest/', params='', cookies=None, timeout=0, headers={}):
        '''GET(resource)
        Function executes a GET call to a given resource and returns a result converted to the Python list
    
        A class variable "reply" always contains the latest output of the hub for any call (GET, POST, PUT or DELETE)
        "reply.status_code" contains status code, it is 200 if the latest call was ok
        if not then further information could be obtained by "reply.reason"
        also "reply.text" contains raw output of the latest call:
        '''
        return self._request('get', resource, '', service, interface, params, cookies, timeout, headers)

    def POST(self, resource, payload = '', service = '', interface = '/rest/', cookies=None, timeout=0, headers={}):
        '''POST(resource, payload)
        Function executes a POST call to a given resource with a given parameters
        and returns a result converted to the Python list
    
        A class variable "reply" always contains the latest output of the hub for any call (GET, POST, PUT or DELETE)
        "reply.status_code" contains status code, it is 200 if the latest call was ok
        if not then further information could be obtained by "reply.reason"
        also "reply.text" contains raw output of the latest call:
        '''
        return self._request('post', resource, payload, service, interface, cookies, timeout, headers)

    def PUT(self, resource, payload, service = '', interface = '/rest/', cookies=None, timeout=0, headers={}):
        '''PUT(resource, payload)
        Function executes a PUT call to a given resource with a given parameters
        and returns a result converted to the Python list
    
        A class variable "reply" always contains the latest output of the hub for any call (GET, POST, PUT or DELETE)
        "reply.status_code" contains status code, it is 200 if the latest call was ok
        if not then further information could be obtained by "reply.reason"
        also "reply.text" contains raw output of the latest call:
        '''
        return self._request('put', resource, payload, service, interface, cookies, timeout, headers)

    def DELETE(self, resource, payload = '', service = '', interface = '/rest/', cookies=None, timeout=0, headers={}):
        '''DELETE(resource) or DELETE(resource, payload)
        Function executes a DELETE call to a given resource with a given parameters (if no parameters needed, they could be omitted)
        and returns a result converted to the Python list
    
        A class variable "reply" always contains the latest output of the hub for any call (GET, POST, PUT or DELETE)
        "reply.status_code" contains status code, it is 200 if the latest call was ok
        if not then further information could be obtained by "reply.reason"
        also "reply.text" contains raw output of the latest call:
        '''
        return self._request('delete', resource, payload, service, interface, cookies, timeout, headers)
    def print(self, a, sort_keys=True, indent=4):
        print(json.dumps(a, sort_keys=sort_keys, indent=indent))

#a small function that tests if a given argument is a correct IPv4 address
def validIP(address):
    '''A small function that tests if a given argument is a correct IPv4 address
    '''
    address = address.split(':')[0]
    if address == 'localhost': return True
    parts = address.split(".")
    if len(parts) != 4:
        return False
    for item in parts:
        try:
            if not 0 <= int(item) <= 255:
                return False
        except ValueError:
            return False 
    return True

def isString(a):
    return isinstance(a, str) or isinstance(a, unicode)

if __name__=='__main__':
    from sys import argv
    if len(argv) > 1: 
        ip = argv[1]
    else:
        ip = ""
    if len(argv) > 2: 
        username = argv[2]
    else:
        username = ""
    if len(argv) > 3: 
        password = argv[3]
    else:
        password = ""
    if ip != "":
        if username != "":
            if password != "":
                rest = REST(ip, username, password)
            else:
                rest = REST(ip, username)
        else:
            rest = REST(ip)
