#DIALOG VERSION: 2.2.2
import os
import platform
import yaml
import logging
import argparse
import json
from socket import gethostname
import math
import time

host_name = ''

def file_has_changed(file, prev_modified_date, active_hps=None):
    if active_hps is not None:
        file = file.format(active_hps)
    try:
        modified_date = os.path.getmtime(unicode(file))
        return (modified_date > prev_modified_date, modified_date)
    except:
        logging.exception("'{0}' can not be found".format(file))
        return (False, 0)

def read_single_line(file):
    with open(file, 'r') as f:
        return f.read()

def read_lines(file, active_hps=None):
    if active_hps is not None:
        file = file.format(active_hps)
    with open(file, 'r') as f:
        return f.readlines()

def read_yaml(file, active_hps=None):
    if active_hps is not None:
        file = file.format(active_hps)
    with open(file, 'r') as f:
        return yaml.safe_load(f)

def ntc_active_if_name():
    return 'ntc-active-hps'

def p2pvconnection_name():
    return 'p2pvconnection'

def bdm_roles_name():
    return 'bdm_roles'

def multicast_name():
    return 'multicast'

def terminals_name():
    return 'terminals'

def rtm_terminals_name():
    return 'rtm_terminals'

def ts_encap_root_name():
    return 'encap_root'

def tn_instances_name():
    return 'tellinet_instances'

def fwd_link_name():
    return 'fwd_link'

def rtn_link_name():
    return 'rtn_link'

def ntc_active_if():
    if 'windows' in platform.system().lower():
        return "{0}{1}".format(sharedfs_if_location(), ntc_active_if_name())

    return '/var/run/{0}'.format(ntc_active_if_name())

def sharedfs_if_location():
    if 'windows' in platform.system().lower():
        return './test_config/'

    return '/mnt/sharedfs/version_DIALOG_FACTORY/HPS-{0}'

def rtmc_source_location(file_name):
    if 'windows' in platform.system().lower():
        return "{0}{1}".format(sharedfs_if_location(), file_name)

    return '{0}/rtmc/{1}'.format(sharedfs_if_location(), file_name)

def amp_source_location(file_name):
    if 'windows' in platform.system().lower():
        return "{0}{1}".format(sharedfs_if_location(), file_name)

    return '{0}/amp/cfg/{1}'.format(sharedfs_if_location(), file_name)

def bdm_roles():
    if 'windows' in platform.system().lower():
        return "{0}{1}".format(sharedfs_if_location(), '{0}.yaml'.format(bdm_roles_name()))

    return amp_source_location('{0}.yaml'.format(bdm_roles_name()))

def ts_encap_location(file_name):
    if 'windows' in platform.system().lower():
        return "{0}{1}".format(sharedfs_if_location(), file_name)

    return '{0}/ts_encap/cfg/config/{1}'.format(sharedfs_if_location(), file_name)

def local_rest_endpoint():
    if 'windows' in platform.system().lower():
        #assuming local REST API simulation runs on port 8000
        return 'http://192.168.86.43/'

    return 'http://127.0.0.1/'

def amp_local_url(src_host, src_port, satnet_if, amp_instance_id, suffix):
    if 'windows' in platform.system().lower():
        #local testing assumes regular Dialog 2.1.2 1IF/4IF deployment
        return 'http://{0}:{1}/remote-gui/dia9/CPMCTL-{2}/amp{3}{4}'.format(src_host, src_port, satnet_if, amp_instance_id, suffix)

    return 'http://{0}:{1}/amp{2}{3}'.format(src_host, src_port, amp_instance_id, suffix)


def hrcctl_local_url(src_host, src_port, satnet_if, suffix):
    if 'windows' in platform.system().lower():
        return 'http://{0}:{1}/remote-gui/dialog7/HRCCTL-{2}/{3}'.format(src_host, src_port, satnet_if, suffix)

    return 'http://{0}:{1}/{2}'.format(src_host, src_port, suffix)

def tcs_local_url(src_host, src_port, satnet_if, suffix):
    if 'windows' in platform.system().lower():
        return 'http://{0}:{1}/remote-gui/dia9/tcs-{2}-0/{3}'.format(src_host, src_port, satnet_if, suffix)

    return 'http://{0}:{1}/{2}'.format(src_host, src_port, suffix)

def get_config(config, module_name, key):
    exception_format = 'Module {0} is missing input configuration key/value: {1}'
    if key in config:
        return config[key]
    else:
        logging.error(exception_format.format(module_name, key))
        return ''
    
class RunMode:
    DAEMON = 0
    RUNONCE = 1
    MOCK = 2

run_modes = { 'DAEMON': RunMode.DAEMON, 'RUNONCE': RunMode.RUNONCE, 'MOCK': RunMode.MOCK}

def get_run_mode(run_mode):
    if run_mode in run_modes:
        return run_modes[run_mode]

    return RunMode.DAEMON

logging_levels = { 'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL, 'TRACE': 15 }

def get_log_level(log_level):
    if log_level in logging_levels.keys():
        return logging_levels[log_level]
    return logging.INFO

def arg_parser():
    if 'windows' in platform.system().lower():
        default_log_path = 'c:/temp/rtm-collector.log'
    else:
        default_log_path = '/var/log/rtm-collector/rtm-collector.log'

    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', help = 'Polling interval. Default value: 10s', type = int, default = 10)
    parser.add_argument('--log', help = 'Location of the logfile. Default value: {0}'.format(default_log_path), type = str, default = default_log_path)
    parser.add_argument('--loglevel', help = 'Loglevel. Default value: INFO', type = str, default = 'INFO')
    parser.add_argument('--host', help = 'Destination host for the collected metrics. Default value: localhost', type = str, default = 'localhost')
    parser.add_argument('--port', help = 'Destination port for the collected metrics. Default value: 8186', type = int, default = 8186)
    parser.add_argument('--database', help = 'Database to store the collected metrics. Default value: telegraf', type = str, default = 'telegraf')
    parser.add_argument('--mode', help = 'How this script is run: DAEMON | RUNONCE. Default value: DAEMON', type = str, default = 'RUNONCE')
    parser.add_argument('--prov', help = 'Provosioning data location represented as a json key/value collection. Could be used to pass in provisioning related arguments. No default value', type = json.loads)
    parser.add_argument('--src-host', help = 'ip address of the source to be queried', type = str, default = '127.0.0.1')
    parser.add_argument('--src-port', help = 'port of the source to be queried', type = int, default = 10210)    
    parser.add_argument('--fallible', help='flag to indicate if the collector is allowed to fail (used for testing)', type=bool, default = False)
    parser.add_argument('--config', help = 'location + filename of a yaml file containing all possible config', type = str, default = './test_config/base_config.yaml')
    args = parser.parse_args()
    return args
'''
return :
Namespace(config='./test_config/base_config.yaml', database='telegraf', fallible=False, host='localhost', interval=10, log='c:/temp/rtm-collector.log', loglevel='INFO', mode='RUNONCE', port=8186, prov=None, src_host='127.0.0.1', src_port=10210)
'''


class CollectorConfig(dict):
    def __getattr__(self, item):   # #调用类中原本没有定义的属性时候，调用__getattr__
        if item in self:
            return self[item]
        return None

    def __setattr__(self, item, value): ##对实例的属性进行赋值的时候调用__setattr__
        self[item] = value

def parse_config():
    args = arg_parser()


    '''
    生成一个对象。
    '''
    collector_config = CollectorConfig()

    if args.config != None and args.config != '':
        '''
        read './test_config/base_config.yaml'
        '''
        config_yaml = read_yaml(args.config)

        if 'config' in config_yaml and config_yaml['config'] != None:
            if 'interval' in config_yaml['config']:
                collector_config.interval = config_yaml['config']['interval']

    if collector_config.interval == None:
        collector_config.interval = args.interval
    if collector_config.log == None:
        collector_config.log = args.log
    if collector_config.loglevel == None:
        collector_config.loglevel = args.loglevel
    if collector_config.host == None:
        collector_config.host = args.host
    if collector_config.port == None:
        collector_config.port = args.port
    if collector_config.database == None:
        collector_config.database = args.database
    if collector_config.mode == None:
        collector_config.mode = args.mode
    if collector_config.prov == None:
        collector_config.prov = args.prov
    if collector_config.src_host == None:
        collector_config.src_host = args.src_host
    if collector_config.src_port == None:
        collector_config.src_port = args.src_port
    if collector_config.fallible == None:
        collector_config.fallible = args.fallible

    return collector_config


def configure_logging(file_name, log_level, name):
    logging_format = '%(levelname)-10s: %(asctime)s : {name} : %(message)s'.format(name=name)
    logging.basicConfig(filename = file_name, level = get_log_level(log_level), format = logging_format)
    logging.addLevelName(15, "TRACE")
    
    #suppres unwanted log message from the requests lib
    logging.getLogger("requests").setLevel(logging.ERROR)
    #urllib3 is used by requests and can also spam the log file
    logging.getLogger("urllib3").setLevel(logging.ERROR)

def get_default_args(value, arg_value):
    if arg_value == None:
        return value
    if type(arg_value) == dict:
        value.update(arg_value)
        return value
    return arg_value

def raise_value_error(message):
    logging.error(message)
    raise ValueError(message)

def get_host_name():
    global host_name

    if host_name == '':
        host_name = gethostname()

    return host_name

def get_polling_time(interval):
    tm = time.time()
    return int(math.floor(tm / float(interval))) * int(interval)

def get_total_seconds(time_delta):
    result = time_delta.seconds + time_delta.days * 24 * 3600
    return result

