#DIALOG VERSION: 2.2.2
import L2_DEM_interface_stats
import L2_DEM_terminal_stats
import sys
from time import time
from socketmetricscollector import SocketMetricsCollector, MockSocketMetricsCollector
import ConfigParser
from telegrafpy import TMetric
import time
import ntc_tools
from itertools import chain
import requests
import logging
import ntc_daemon
import ntc_main


general_statistics_commands = ['get statistics.by_node_name.{0}_layer2.received_bytes\n',
        'get statistics.by_node_name.{0}_layer2.received_packets\n',
        'get statistics.by_node_name.{0}_layer2.sent_bytes\n',
        'get statistics.by_node_name.{0}_layer2.sent_packets\n']

terminal_statistics_commands = ['get statistics.by_node_name.sit_{0}_{1}_l2{2}.received_bytes\n',
    'get statistics.by_node_name.sit_{0}_{1}_l2{2}.received_packets\n',
    'get statistics.by_node_name.sit_{0}_{1}_l2{2}.sent_bytes\n',
    'get statistics.by_node_name.sit_{0}_{1}_l2{2}.sent_packets\n']

terminal_commands = []
terminal_provisioning_data = []

satnet_if = 0
ntc_active_if_modified = 0
provisioned_terminals_modified = 0
ntc_active_if_file_name = ''
provisioned_terminals_p2pvc_file_name = ''
terminal_p2pvc_provisioning_data = [] 
provisioned_tellinet_ip_port = []

def register(config):
    global ntc_active_if_file_name
    global provisioned_terminals_p2pvc_file_name
    global multicast_terminals_file_name
    global provisioned_tellinet_ip_port 

    module_name = 'L2_DEM_stats'

    ntc_active_if_file_name = ntc_tools.get_config(config, module_name, ntc_tools.ntc_active_if_name())
    provisioned_terminals_p2pvc_file_name = ntc_tools.get_config(config, module_name, ntc_tools.p2pvconnection_name())
    provisioned_tellinet_ip_port = [int(ntc_tools.get_config(config, module_name, 'l2fwd_src_port')), int(ntc_tools.get_config(config, module_name, 'l2rtn_src_port'))]
    
def initialize():
    pass

def read(args):
    global satnet_if
    global ntc_active_if_modified
    global provisioned_terminals_modified
    global terminal_provisioning_data
    global terminal_commands
    global terminal_statistics_commands
    global terminal_p2pvc_provisioning_data
    global provisioned_tellinet_ip_por
    global provisioned_terminals_p2pvc_file_name
    active_if_changed = False

    tm = time.time()

    #check if '/var/ntc-active-if' has changed (first run, this will always be
    #the case)
    (file_modified, modified_date) = ntc_tools.file_has_changed(ntc_active_if_file_name, ntc_active_if_modified)
    if file_modified:
        ntc_active_if_modified = modified_date
        satnet_if = ntc_tools.read_single_line(ntc_active_if_file_name)
        active_if_changed = True

    fwd_interfaces_commands = [command.format('forward') for command in general_statistics_commands]
    rtn_interfaces_commands = [command.format('return') for command in general_statistics_commands]

    #return & forward metrics for general interfaces
    interface_metrics_forward = L2_DEM_interface_stats.get(args.src_host, provisioned_tellinet_ip_port[0], satnet_if, fwd_interfaces_commands, 'fwd', tm)
    interface_metrics_return = L2_DEM_interface_stats.get(args.src_host, provisioned_tellinet_ip_port[1], satnet_if, rtn_interfaces_commands, 'rtn', tm)
   
    #--------- TERMINALS ---------
    #check if terminals file was changed
    if provisioned_terminals_p2pvc_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(provisioned_terminals_p2pvc_file_name, provisioned_terminals_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            #re-set modified date for next run
            provisioned_terminals_modified = modified_date
            content = ntc_tools.read_lines(provisioned_terminals_p2pvc_file_name, active_hps=satnet_if)
            terminal_p2pvc_provisioning_data = [x.strip().split('|') for x in content]
            #compose list of terminal commands based on terminal id and
            #point to point connection id
            terminal_commands = []
            for terminal_data in terminal_p2pvc_provisioning_data:
               terminal_id = terminal_data[0]
               p2pvc_id = terminal_data[1]
               terminal_commands.extend([terminal_command.format(terminal_id, p2pvc_id,'{0}') for terminal_command in terminal_statistics_commands])  

    #return & forward statistics for terminals
    collector = SocketMetricsCollector()
    if ntc_tools.get_run_mode(args.mode) == ntc_tools.RunMode.MOCK:
        collector = MockSocketMetricsCollector()
    terminal_rtn_stats = L2_DEM_terminal_stats.get(collector, args.src_host, provisioned_tellinet_ip_port[0], satnet_if, args.pointToPointConnectionid, terminal_p2pvc_provisioning_data, terminal_commands, 'fwd', tm)
    terminal_forward_stats = L2_DEM_terminal_stats.get(collector, args.src_host, provisioned_tellinet_ip_port[0], satnet_if, args.pointToPointConnectionid, terminal_p2pvc_provisioning_data, terminal_commands, 'rtn', tm)

    return chain(interface_metrics_forward,interface_metrics_return, terminal_rtn_stats, terminal_forward_stats)


if __name__ == "__main__":
    default_config = { 
        ntc_tools.ntc_active_if_name(): ntc_tools.ntc_active_if(), 
        ntc_tools.terminals_name(): ntc_tools.rtmc_source_location('terminals'), 
        ntc_tools.multicast_name(): ntc_tools.rtmc_source_location('multicastcircuits'), 
        ntc_tools.p2pvconnection_name(): ntc_tools.rtmc_source_location('p2pvconnection'), 
        'l2fwd_src_port': 15132, 
        'l2rtn_src_port': 15135, 
        }
    default_port = 10210
    ntc_main.main(default_config, default_port, register, read, "L2_DEM_stats")