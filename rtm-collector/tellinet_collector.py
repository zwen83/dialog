#DIALOG VERSION: 2.2.2
import time
import ConfigParser
import ntc_tools
from telegrafpy import TMetric
from socketmetricscollector import SocketMetricsCollector, MockSocketMetricsCollector
from multiprocessing.dummy import Pool
from functools import partial
import logging
import ntc_daemon
import ntc_main

##############################################################################
# global variables and constants initial values
##############################################################################

#template of commands per Tellinet instance
tn_telnet_cmd_wrapper = 'get {0}\n'
tn_telnet_template_prefix_per_instance = tn_telnet_cmd_wrapper.format('statistics.{0}')
tn_telnet_template_per_instance = ['associations.count', 'etcp.connections.count', 'used_memory']

#template of commands per L3 Network
tn_telnet_templace_gtp_prefix_per_network = tn_telnet_cmd_wrapper.format('statistics.user_mode_ip_stack.by_virtual_network.net-{0}.{1}')
tn_telnet_template_gtp_metrics = ['gtp_tunnel.count_net2sat', 'gtp_tunnel.count_sat2net', 'gtp_tunnel.count_duplex', 'gtp_tunnel.count_tcp', 'tcp.count_tcp']

#list of Tellinet instances
tn_instances = []
#configuration file settings
satnet_config_filename = ''
satnet_config_file_last_modified = 0
tn_config_filename = ''
tn_config_file_last_modified = 0
satnet = 0

#other globals
poll_timestamp = 0
MAX_THREAD_COUNT = 100

##############################################################################
#tellinet instance info
##############################################################################
class TnInstanceInfo:
    TN_TELNET_CMDS_KEY_PER_INSTANCE = 'per-instance'

    def __init__(self, satnet, instance_id, instance_ip, instance_port, vrf_ids):
        self.tn_instance_id = instance_id
        self.tn_instance_ip = instance_ip
        self.tn_instance_port = int(instance_port)
        self.vrf_ids = vrf_ids
        self.instance_tags = {
            'type' : 'tellinet',
            'hps' : satnet,
            'tn_instance_id' : self.tn_instance_id,
        }
        #add basic per-instance commands
        self.telnet_cmds = dict((tn_telnet_template_prefix_per_instance.format(cmd), (self.TN_TELNET_CMDS_KEY_PER_INSTANCE, cmd)) for cmd in tn_telnet_template_per_instance)
        #prepare telnet commands for each network ID
        for net_id in self.vrf_ids.keys():
            if net_id == '':
                continue
            self.telnet_cmds.update(dict((tn_telnet_templace_gtp_prefix_per_network.format(net_id, metric), (net_id, metric)) for metric in tn_telnet_template_gtp_metrics))
        #print str(self.tn_instance_port) + " : " + str(self.telnet_cmds)

    def repack_data(self, poll_timestamp, telnet_data):
        """ Repacks telnet return data into a list of TMetric objects """
        idb_metrics = {}
        for datum in telnet_data:
            #print "[" + str(self.tn_instance_id) + ":" +
            #str(datum.full_metric) + ":" + str(datum.value) + "]\n"
            cmd = tn_telnet_cmd_wrapper.format(datum.full_metric)
            if cmd not in self.telnet_cmds:
                continue
            (net_id, metric) = self.telnet_cmds[cmd]
            if net_id not in idb_metrics:
                tags = self.instance_tags.copy()
                if net_id != self.TN_TELNET_CMDS_KEY_PER_INSTANCE: tags['vrf_id'] = self.vrf_ids[net_id]
                idb_metrics[net_id] = TMetric('tas', poll_timestamp, tags, {})
            idb_metrics[net_id].fields[metric] = datum.value
        #return all metrics as one list
        return idb_metrics.values()


##############################################################################
#collector-specific functionality
##############################################################################
def check_load_config(args):
    global tn_instances
    global satnet_config_file_last_modified
    global tn_config_file_last_modified
    global satnet
    active_if_changed = False
    
    #check if '/var/ntc-active-hps' has changed (contains satnet ID)
    (file_modified, modified_date) = ntc_tools.file_has_changed(satnet_config_filename, satnet_config_file_last_modified)
    if file_modified:
        #re-set modifief date for next run
        satnet_config_file_last_modified = modified_date
        satnet = ntc_tools.read_single_line(ntc_tools.ntc_active_if()).strip()
        active_if_changed = True

    #check if config file has changed
    if tn_config_filename != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(tn_config_filename.format(satnet), tn_config_file_last_modified, active_hps=satnet)
        if file_modified or active_if_changed:
            #re-set modified date for next run
            tn_config_file_last_modified = modified_date
            content = ntc_tools.read_lines(tn_config_filename, active_hps=satnet)
            tn_instances = []

            for line in [l.strip() for l in content]:
                #anything starting with # is line-comment, so remove text after
                line = line.split('#')[0]
                #skip empty lines
                if line == '':
                    continue
                #check for instances; multiples allowed
                if line.startswith('tn_instance='):
                    #each instance has ip:port, followed by network IDs after ;
                    info = line.split('=')[1].split(';')
                    instance_id = info[0]
                    instance_port = info[1]
                    if info[2] != '' and ',' in info[2] and '|' in info[2]:
                        vrf_ids = dict(id_tpl.strip().split('|') for id_tpl in info[2].split(','))
                        tn_instances.append(TnInstanceInfo(satnet, instance_id, args.src_host, instance_port, vrf_ids))

def collect_instance_data(tn_info, collector):
    data = collector.execute(tn_info.tn_instance_ip, tn_info.tn_instance_port, tn_info.telnet_cmds.keys())
    #repack return data into TMetric objects
    return tn_info.repack_data(poll_timestamp, data)


##############################################################################
#telegraf plugin functions
##############################################################################
def register(config):
    global satnet_config_filename
    global tn_config_filename
    module_name = 'tellinet_collector'
    satnet_config_filename = ntc_tools.get_config(config, module_name, ntc_tools.ntc_active_if_name())
    tn_config_filename = ntc_tools.get_config(config, module_name, ntc_tools.tn_instances_name())

def initialize():
    pass

def read(args):
    global poll_timestamp
    check_load_config(args)
    poll_timestamp = ntc_tools.get_polling_time(args.interval)
    
    all_metric_lists = []
    if len(tn_instances) > 0:
        pool = Pool(MAX_THREAD_COUNT)
        collector = SocketMetricsCollector()
        if ntc_tools.get_run_mode(args.mode) == ntc_tools.RunMode.MOCK:
            collector = MockSocketMetricsCollector()
        collect_instance_data_partial = partial(collect_instance_data, collector=collector)
        all_metric_lists = pool.map(collect_instance_data_partial, tn_instances)
        pool.close()
        pool.join()

    #return as generator instead of list due to plugin requirements
    return ( metric for all_metrics in all_metric_lists for metric in all_metrics )

##############################################################################
#main function for use in testing
##############################################################################
if __name__ == "__main__":
    default_config = { 
        ntc_tools.ntc_active_if_name(): ntc_tools.ntc_active_if(), 
        ntc_tools.tn_instances_name() : ntc_tools.rtmc_source_location('tellinet_instances'),
        }
    default_port = 10210
    ntc_main.main(default_config, default_port, register, read, "tellinet_collector")