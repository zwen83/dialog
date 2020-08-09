#DIALOG VERSION: 2.2.2
import sys
from time import time
import ConfigParser

from socketmetricscollector import SocketMetricsCollector, MockSocketMetricsCollector
from telegrafpy import TMetric
import time
import rtn_shaper_terminal_stats
import rtn_shaper_terminal_multicast_stats
import ntc_tools
from itertools import chain
import requests
import logging
import ntc_daemon
import rtn_shaper_link_stats
import rtn_link_tools
import ntc_main

qos_terminal_commands = [
        'get statistics.by_node_name.sit_{0}_{1}.received_bytes\n',
        'get statistics.by_node_name.sit_{0}_{1}.received_packets\n',
    ]

multicast_commands = [
        'get statistics.by_node_name.multicast_{0}.received_bytes\n'
        'get statistics.by_node_name.multicast_{0}.received_packets\n'
    ]

terminal_ids = []
multicast_data = {}
satnet_if = 0
ntc_active_if_modified = 0
provisioned_terminals_modified = 0
multicast_terminals_modified = 0
rtn_shaper_terminal_commands = []
rtn_shaper_multicast_commands = []
ntc_active_if_file_name = ''
provisioned_terminals_file_name = ''
multicast_terminals_file_name = ''
terminal_provisioning_data = []
rtn_link_file_name = ''
rtn_link_modified = 0
rtn_link_commands = []
rtn_link_provisioning = None

def register(config):
    global ntc_active_if_file_name
    global provisioned_terminals_file_name
    global multicast_terminals_file_name
    global rtn_link_file_name

    module_name = 'rtn_shaper_stats'

    ntc_active_if_file_name = ntc_tools.get_config(config, module_name, ntc_tools.ntc_active_if_name())
    provisioned_terminals_file_name = ntc_tools.get_config(config, module_name, ntc_tools.terminals_name())
    multicast_terminals_file_name = ntc_tools.get_config(config, module_name, ntc_tools.multicast_name())
    rtn_link_file_name = ntc_tools.get_config(config, module_name, ntc_tools.rtn_link_name())

def initialize():
    pass

def read(args):
    global satnet_if
    global ntc_active_if_modified

    global terminal_ids
    global provisioned_terminals_modified

    global multicast_data
    global multicast_terminals_modified

    global rtn_shaper_terminal_commands
    global rtn_shaper_multicast_commands

    global terminal_provisioning_data

    global rtn_link_modified
    global rtn_link_commands

    global rtn_link_provisioning
    active_if_changed = False

    tm = ntc_tools.get_polling_time(args.interval)

    #check if '/var/ntc-active-hps' has changed (first run, this will always be the case)
    (file_modified, modified_date) = ntc_tools.file_has_changed(ntc_active_if_file_name, ntc_active_if_modified)
    if file_modified:
        ntc_active_if_modified = modified_date
        satnet_if = ntc_tools.read_single_line(ntc_active_if_file_name)
        active_if_changed = True

    #check if terminals file was changed
    if provisioned_terminals_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(provisioned_terminals_file_name, provisioned_terminals_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            terminal_provisioning_data = []
            #re-set modified date for next run
            provisioned_terminals_modified = modified_date
            content = ntc_tools.read_lines(provisioned_terminals_file_name, active_hps=satnet_if)
            terminal_provisioning_data = [x.strip().split('|') for x in content]
            '''
            [['18074', 'BE'], ['18510', 'BE'], ['11958', 'BE']]
            '''

            # [['700', 'BE'], ['763', 'BE'], ['914', 'BE']]
            #compose list of terminal commands
            rtn_shaper_terminal_commands = []
            for terminal_data in terminal_provisioning_data:
                terminal_id = terminal_data[0]
                for qos_class in terminal_data[1:]:
                    rtn_shaper_terminal_commands.extend([ terminal_command.format(terminal_id, qos_class) for terminal_command in qos_terminal_commands ])
            '''
            ['get statistics.by_node_name.sit_18074_BE.received_bytes\n', 
            'get statistics.by_node_name.sit_18074_BE.received_packets\n', 
            'get statistics.by_node_name.sit_18510_BE.received_bytes\n', 
            'get statistics.by_node_name.sit_18510_BE.received_packets\n', 
            'get statistics.by_node_name.sit_11958_BE.received_bytes\n', 
            'get statistics.by_node_name.sit_11958_BE.received_packets\n']

            '''
    #check if multicast file was changed
    if multicast_terminals_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(multicast_terminals_file_name, multicast_terminals_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            #re-set modified date for next run
            multicast_terminals_modified = modified_date
            content = ntc_tools.read_lines(multicast_terminals_file_name, active_hps=satnet_if)
            #file contains all multicast-ids & associated terminal_ids separated by '|' => one 'multicast_id|terminal_id' per line
            #content is parsed into a dictionary. Multicast_id = key, value is a set (=>contains unique items) of terminal_ids. A multicast_id can be in use by multiple terminals
            multicast_data = {}
            for line in content:
                splits = line.strip().split('|')
                multicast_id = splits[0]
                terminal_id = splits[1]
                multicast_data[multicast_id] = terminal_id

            #compose list of multicast commands
            rtn_shaper_multicast_commands = []
            for multicast_id in multicast_data.keys():
                rtn_shaper_multicast_commands.extend([multicast_command.format(multicast_id) for multicast_command in multicast_commands])

    if rtn_link_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(rtn_link_file_name, rtn_link_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            rtn_link_modified = modified_date
            rtn_link_provisioning = ntc_tools.read_yaml(rtn_link_file_name, active_hps=satnet_if)
            rtn_link_commands = []
            if rtn_link_provisioning != None and 'rtn-link-id' in rtn_link_provisioning:
                parser = rtn_link_tools.RtnLinkConfigParser(rtn_link_provisioning)
                rtn_link_commands = parser.get_commands()
    
    #execute all commands
    collector = SocketMetricsCollector()
    if ntc_tools.get_run_mode(args.mode) == ntc_tools.RunMode.MOCK:
        collector = MockSocketMetricsCollector()
    satnet_stats = rtn_shaper_link_stats.get(collector, args.src_host, args.src_port, satnet_if, rtn_link_provisioning, rtn_link_commands, tm)
    terminal_stats = rtn_shaper_terminal_stats.get(collector, args.src_host, args.src_port, satnet_if, rtn_shaper_terminal_commands, terminal_provisioning_data, tm)
    '''
    <generator object get at 0x20a2af0>
    '''
    multicast_stats = rtn_shaper_terminal_multicast_stats.get(collector, args.src_host, args.src_port, satnet_if, rtn_shaper_multicast_commands, multicast_data, tm)

    return chain(terminal_stats, multicast_stats, satnet_stats)

if __name__ == "__main__":
    default_config = { 
        ntc_tools.ntc_active_if_name(): ntc_tools.ntc_active_if(), 
        ntc_tools.terminals_name(): ntc_tools.rtmc_source_location('rtn_terminals'), 
        ntc_tools.multicast_name(): ntc_tools.rtmc_source_location('multicastcircuits'), 
        ntc_tools.rtn_link_name(): ntc_tools.rtmc_source_location('{0}.yaml'.format(ntc_tools.rtn_link_name())),
        }
    default_port = 10210
    ntc_main.main(default_config, default_port, register, read, "rtn_shaper_stats")




'''

config:
  interval: 30
  log: /var/log/rtm-collector/rtm-collector.log
  loglevel: INFO
  host: localhost
  port: 8186
  database: telegraf
  src_host: 127.0.0.1
  src_port: 10210
  mode: RUNONCE
  prov: { 'multicast':'/var/ntc-active-if/rtmc/multicastcircuits', 'ntc-active-if':'/var/run/ntc-active-if', 'rtn_link':'/var/ntc-active-if/rtmc/rtn_link.yaml', 'terminals':'/var/ntc-active-if/rtmc/rtn_terminals'}


1) 'rtn_link':'/var/ntc-active-if/rtmc/rtn_link.yaml'

rtn-link-id: 682
return-capacity-groups:
   - return-capacity-group:
      id: 744
      return-technology: s2
   - return-capacity-group:
      id: 846
      return-technology: cpm
   - return-capacity-group:
      id: 695
      return-technology: hrc_mxdma

2) 'ntc-active-if':'/var/run/ntc-active-if'
1

3) 'terminals':'/var/ntc-active-if/rtmc/rtn_terminals'
700|BE
763|BE
914|BE

'''