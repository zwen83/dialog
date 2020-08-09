ip = '192.168.35.60'
username = 'hno'
password = 'D!@10g'

domain = 'vno'
modem = '3000252'

__author__  = 'isim'
__version__ = 1.21
import logging
from rest import REST
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fh = logging.FileHandler(__name__+'.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)
# Edit here to match the SN name. Note that for BHI, it ends with e.g. SN1, but JAV ends with SN-1
logging.getLogger('rest').setLevel(logging.DEBUG)


rest = REST(ip, username=username, password=password)
terminal = rest.GET('modem/%s/%s' % (domain, modem))
hubmodule = rest.GET('hub-module')
print(terminal)
if terminal and type(terminal) == dict and 'id' in terminal:
    terminalId = terminal['id']['systemId']
    hubmodule = terminal['remoteGuiUrl'].split("/")[1]
    print(hubmodule)
else:
    print('Terminal %s/%s was not found or communication error' % (domain, modem))
    exit(1)
if 'tcs-1-0' in terminal['remoteGuiUrl']:
    satnet = 1
elif 'tcs-2-0' in terminal['remoteGuiUrl']:
    satnet = 2
elif 'tcs-3-0' in terminal['remoteGuiUrl']:
    satnet = 3
elif 'tcs-4-0' in terminal['remoteGuiUrl']:
    satnet = 4

# {}_ENCL-1

logger.info('Rebooting terminal %s/%s in SatNet-%i with id=%i' % (domain, modem, satnet, terminalId))

service = '/remote-gui/%s/CSE-%i-0/ftb-device-manager' % (hubmodule,satnet)
rest.POST('lifecycle/terminal/%i/reboot' % terminalId,'',service)
