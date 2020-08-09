#DIALOG VERSION: 2.2.2
import cpmctl_terminal_stats
import cpmctl_satnet_stats
import ntc_tools
import ntc_main
import time
from itertools import chain
import logging
import ntc_daemon
import requests

satnet_if = 0
amp_instances = 0
ntc_active_if_modified = 0
bdm_roles_modified = 0
multicast_terminals_modified = 0
multicast_data = {}
ntc_active_if_file_name = ''
bdm_roles_file_name = ''
multicast_terminals_file_name = ''
provisioned_terminals_file_name = ''
provisioned_terminals_modified = 0

terminal_ids = []

def register(config):
    global ntc_active_if_file_name
    global bdm_roles_file_name
    global multicast_terminals_file_name
    global provisioned_terminals_file_name

    module_name = 'cpmctl_stats'

    ntc_active_if_file_name = ntc_tools.get_config(config, module_name, ntc_tools.ntc_active_if_name())
    bdm_roles_file_name = ntc_tools.get_config(config, module_name, ntc_tools.bdm_roles_name())
    multicast_terminals_file_name = ntc_tools.get_config(config, module_name, ntc_tools.multicast_name())
    provisioned_terminals_file_name = ntc_tools.get_config(config, module_name, ntc_tools.terminals_name())

def initialize():
    pass

def read(args):
    global satnet_if
    global amp_instances
    global ntc_active_if_modified
    global bdm_roles_modified
    global multicast_terminals_modified
    global multicast_data
    global provisioned_terminals_modified
    global terminal_ids
    active_if_changed = False

    tm = ntc_tools.get_polling_time(args.interval)

    #check if '/var/ntc-active-hps' has changed (first run, this will always be the case)
    (file_modified, modified_date) = ntc_tools.file_has_changed(ntc_active_if_file_name, ntc_active_if_modified)
    if file_modified:
        #re-set modifief date for next run
        ntc_active_if_modified = modified_date
        satnet_if = ntc_tools.read_single_line(ntc_active_if_file_name)
        active_if_changed

    if bdm_roles_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(bdm_roles_file_name, bdm_roles_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            #re-set modified data for next run
            bdm_roles_modified = modified_date
            #re-read bdm_roles.yaml
            bdm_roles_yaml = ntc_tools.read_yaml(bdm_roles_file_name, active_hps=satnet_if)
            #re-set amp_instances
            amp_instances = []
            [amp_instances.append(key) for key, value in bdm_roles_yaml['bdm_roles'].iteritems()]

    if multicast_terminals_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(multicast_terminals_file_name, multicast_terminals_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            #re-set modified date for next run
            multicast_terminals_modified = modified_date
            #re-read multicast & terminal ids
            content = ntc_tools.read_lines(multicast_terminals_file_name, active_hps=satnet_if)
            multicast_data = {}
            for line in content:
                splits = line.strip().split('|')
                multicast_id = splits[0]
                terminal_id = splits[1]
                multicast_data[multicast_id] = terminal_id

    #check if terminals file was changed
    if provisioned_terminals_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(provisioned_terminals_file_name, provisioned_terminals_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            terminal_ids = []
            #re-set modified date for next run
            provisioned_terminals_modified = modified_date
            content = ntc_tools.read_lines(provisioned_terminals_file_name, active_hps=satnet_if)
            terminal_provisioning_data = [x.strip().split('|') for x in content]
            terminal_ids = [int(terminal_data[0]) for terminal_data in terminal_provisioning_data]
    
    result_stats = []
    for amp_instance_id in amp_instances:
        reset_url = ntc_tools.amp_local_url(args.src_host, args.src_port, satnet_if, amp_instance_id, '/stats/execute?action=end_aggregation')
        sit_url = ntc_tools.amp_local_url(args.src_host, args.src_port, satnet_if, amp_instance_id, '/stats/sit')
        shapingnode_url = ntc_tools.amp_local_url(args.src_host, args.src_port, satnet_if, amp_instance_id, '/stats/shapingnode')
        amp_stats_url = ntc_tools.amp_local_url(args.src_host, args.src_port, satnet_if, amp_instance_id, '/stats/amp')
        counter_stats_url = ntc_tools.amp_local_url(args.src_host, args.src_port, satnet_if, amp_instance_id, '/stats/counters')
        slotpoolcontainer_url = ntc_tools.amp_local_url(args.src_host, args.src_port, satnet_if, amp_instance_id, '/stats/slotpoolcontainer')
        carrierpools_url = ntc_tools.amp_local_url(args.src_host, args.src_port, satnet_if, amp_instance_id, '/stats/carrierpool')
        rtcarrier_url = ntc_tools.amp_local_url(args.src_host, args.src_port, satnet_if, amp_instance_id, '/stats/rtcarrier')

        # reset of trackers
        tracker_reset_response = requests.get(reset_url)
        if tracker_reset_response.status_code != 200:
            logging.error("amp instance {0} tracker response code was {1}".format(amp_instance_id, tracker_reset_response.status_code))
            continue

        satnet_stats = cpmctl_satnet_stats.get(amp_stats_url, counter_stats_url, slotpoolcontainer_url, carrierpools_url, rtcarrier_url, shapingnode_url, satnet_if, amp_instance_id, multicast_data, terminal_ids, tm)
        result_stats.append(satnet_stats)

        terminal_stats = cpmctl_terminal_stats.get(sit_url, satnet_if, amp_instance_id, terminal_ids, tm)
        result_stats.append(terminal_stats)
        
    return chain.from_iterable(result_stats)

if __name__ == "__main__":
    default_config = { 
        ntc_tools.ntc_active_if_name(): ntc_tools.ntc_active_if(), 
        ntc_tools.bdm_roles_name() : ntc_tools.bdm_roles(), 
        ntc_tools.multicast_name(): ntc_tools.rtmc_source_location('multicastcircuits'), 
        ntc_tools.terminals_name(): ntc_tools.rtmc_source_location('terminals'), 
        }
    default_port = 80
    ntc_main.main(default_config, default_port, register, read, "cpmctl_stats")