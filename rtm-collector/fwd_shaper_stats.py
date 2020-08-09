#DIALOG VERSION: 2.2.2
import ConfigParser
import ntc_tools
import fwd_shaper_link_stats
import fwd_shaper_terminal_stats
from itertools import chain
import fwd_link_tools
from socketmetricscollector import SocketMetricsCollector, MockSocketMetricsCollector
import ntc_main

general_terminal_commands = [
        'get statistics.by_terminal_name.trm_sit_{0}.modcod\n',
        'get statistics.by_terminal_name.trm_sit_{0}.signalled_cni\n'
    ]

qos_terminal_commands = [
        'get statistics.by_node_name.modem_{0}-{1}.sent_bytes\n',
        'get statistics.by_node_name.modem_{0}-{1}.sent_packets\n',
        'get statistics.by_node_name.modem_{0}-{1}.dropped_bytes\n',
        'get statistics.by_node_name.modem_{0}-{1}.dropped_packets\n',
        'get statistics.by_node_name.modem_{0}-{1}.avg_delay\n',
        'get statistics.by_node_name.modem_{0}-{1}.received_bytes\n',
        'get statistics.by_node_name.modem_{0}-{1}.received_packets\n'
    ]

terminal_ids=[]
terminal_commands = []
terminal_provisioning_data = []

satnet_if = 0
peak_rate = 1.0
ntc_active_if_modified = 0
root_modified = 0
provisioned_terminals_modified = 0
ntc_active_if_file_name = ''
root_file_name = ''
provisioned_terminals_file_name = ''
fwd_link_file_name = ''
fwd_link_modified = 0
fwd_link_config = None

def register(config):
    global ntc_active_if_file_name
    global root_file_name
    global provisioned_terminals_file_name
    global fwd_link_file_name
    global terminal_ids

    module_name = 'fwd_shaper_stats'

    ntc_active_if_file_name = ntc_tools.get_config(config, module_name, ntc_tools.ntc_active_if_name())
    root_file_name = ntc_tools.get_config(config, module_name, ntc_tools.ts_encap_root_name())
    provisioned_terminals_file_name = ntc_tools.get_config(config, module_name, ntc_tools.terminals_name())
    fwd_link_file_name = ntc_tools.get_config(config, module_name, ntc_tools.fwd_link_name())

def initialize():
    pass

def read(args):
    global satnet_if
    global peak_rate
    global ntc_active_if_modified
    global root_modified
    global terminal_ids
    global terminal_commands
    global provisioned_terminals_modified
    global terminal_provisioning_data
    global fwd_link_modified
    global fwd_link_config
    active_if_changed = False

    tm = ntc_tools.get_polling_time(args.interval)

     #check if '/var/ntc-active-hps' has changed (first run, this will always be the case)
    (file_modified, modified_date) = ntc_tools.file_has_changed(ntc_active_if_file_name, ntc_active_if_modified)
    if file_modified:
        #re-set modifief date for next run
        ntc_active_if_modified = modified_date
        satnet_if = ntc_tools.read_single_line(ntc_active_if_file_name)
        active_if_changed = True

    if root_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(root_file_name, root_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            #re-set modified date for next run
            root_modified = modified_date
            #re-read content
            config = ConfigParser.ConfigParser()
            config.read(root_file_name.format(satnet_if))
            fullPeakRate = config.get('root_group', 'peak_rate', 0)
            splitPeakRate = fullPeakRate.split(' ')
            if len(splitPeakRate) > 0:
                peak_rate = float(splitPeakRate[0])

    #check if terminals file was changed
    if provisioned_terminals_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(provisioned_terminals_file_name, provisioned_terminals_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            terminal_provisioning_data = []
            terminal_commands = []
            terminal_ids = []
            #re-set modified date for next run
            provisioned_terminals_modified = modified_date
            content = ntc_tools.read_lines(provisioned_terminals_file_name, active_hps=satnet_if)
            terminal_provisioning_data = [x.strip().split('|') for x in content]
            #compose list of terminal commands
            for terminal_data in terminal_provisioning_data:
                terminal_id = terminal_data[0]
                terminal_ids.append(terminal_id)
                terminal_commands.extend([terminal_command.format(terminal_id) for terminal_command in general_terminal_commands])
                for qos_class in terminal_data[1:]:
                    terminal_commands.extend([ terminal_command.format(terminal_id, qos_class) for terminal_command in qos_terminal_commands ])

    if fwd_link_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(fwd_link_file_name, fwd_link_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            fwd_link_modified = modified_date
            fwd_link_provisioning = ntc_tools.read_yaml(fwd_link_file_name, active_hps=satnet_if)
            if fwd_link_provisioning != None  and 'fwd-link-id' in fwd_link_provisioning:
                fwd_link_config = fwd_link_tools.FwdLinkConfigParser(fwd_link_provisioning)

    collector = SocketMetricsCollector()
    if ntc_tools.get_run_mode(args.mode) == ntc_tools.RunMode.MOCK:
        collector = MockSocketMetricsCollector()

    link_stats_generator = fwd_shaper_link_stats.get(collector, args.src_host, args.src_port, satnet_if, fwd_link_config, peak_rate, tm)
    terminal_stats_generator = fwd_shaper_terminal_stats.get(collector, args.src_host, args.src_port, satnet_if, terminal_ids, terminal_commands, tm)

    return chain(link_stats_generator, terminal_stats_generator)

if __name__ == "__main__":
    default_config = { 
        ntc_tools.ntc_active_if_name(): ntc_tools.ntc_active_if(), 
        ntc_tools.ts_encap_root_name(): ntc_tools.ts_encap_location('root.sdf'), 
        ntc_tools.terminals_name(): ntc_tools.rtmc_source_location('terminals'), 
        ntc_tools.fwd_link_name(): ntc_tools.rtmc_source_location('{0}.yaml'.format(ntc_tools.fwd_link_name())),
        }
    default_port = 10210
    ntc_main.main(default_config, default_port, register, read, "fwd_shaper_stats")