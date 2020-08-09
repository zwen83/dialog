#DIALOG VERSION: 2.2.2
import ntc_tools
import time
import logging
import ntc_daemon
import platform
if 'windows' in platform.system().lower():
    import ntc_snmp_tools as ntc_netsnmp_tools
else:
    import ntc_netsnmp_tools
from telegrafpy import TMetric
import ntc_main

ntc_active_if_file_name = ''
satnet_if = 0
ntc_active_if_modified = 0

snmp_service_stats_columns = { '5835.5.2.3200.1.1.1.2.': 'state', '5835.5.2.3200.1.1.1.3.': 'ESN0', '5835.5.2.3200.1.1.1.4.': 'rx_level'
                             , '5835.5.2.3200.1.1.1.6.': 'frequency_offset', '5835.5.2.3200.1.1.1.7.': 'frame_count'
                             , '5835.5.2.3200.1.1.1.8.': 'dummy_count_count', '5835.5.2.3200.1.1.1.9.': 'errored_frame_count'
                             , '5835.5.2.3200.1.1.1.10.': 'errored_seconds', '5835.5.2.3200.1.1.1.11.': 'tx_power' }

snmp_channel_stats_columns = { '5835.5.2.3200.1.2.1.2.': 'modem_id', '5835.5.2.3200.1.2.1.7.': 'link_margin', '5835.5.2.3200.1.2.1.8.': 'C0D'
                             , '5835.5.2.3200.1.2.1.9.': 'C0N', '5835.5.2.3200.1.2.1.10.': 'C0ND', '5835.5.2.3200.1.2.1.4.': 'modcod' }

snmp_community = 'public'

series_name = 'modem.return.S2_generic'

service_stats_table_oid = '1.3.6.1.4.1.5835.5.2.3200.1.1'
channel_stats_table_oid = '1.3.6.1.4.1.5835.5.2.3200.1.2'

def register(config):
    global ntc_active_if_file_name
    module_name = 's2_stats'

    ntc_active_if_file_name = ntc_tools.get_config(config, module_name, ntc_tools.ntc_active_if_name())

def initialize():
    pass

def read(args):
    global satnet_if
    global ntc_active_if_modified

    tm = ntc_tools.get_polling_time(args.interval)

    #check if '/var/ntc-active-hps' has changed (first run, this will always be the case)
    (file_modified, modified_date) = ntc_tools.file_has_changed(ntc_active_if_file_name, ntc_active_if_modified)
    if file_modified:
        #re-set modifief date for next run
        ntc_active_if_modified = modified_date
        satnet_if = ntc_tools.read_single_line(ntc_active_if_file_name)

    #get the service stats table from snnmp
    service_stats_result = ntc_netsnmp_tools.get_snmp_table(args.src_host, args.src_port, snmp_community
                                                         , ntc_netsnmp_tools.SnmpRequest(service_stats_table_oid, snmp_service_stats_columns.keys()), 11)
    #get the service stats table from snnmp
    channel_stats_result = ntc_netsnmp_tools.get_snmp_table(args.src_host, args.src_port, snmp_community
                                                         , ntc_netsnmp_tools.SnmpRequest(channel_stats_table_oid, snmp_channel_stats_columns.keys()), 9)

    #modem_id is a column in the channel stats table, iso a part of the oid like in the service stats table
    #this code creates a dictionary of modem_id and column_values out of the channel_stats result. This makes it easier to manipulate later
    channel_stats_parsed = {}
    for key, column_values in channel_stats_result.iteritems():
        #if nothing is found (no modem_id column in the result), the modem_id will be set to 0
        modem_id = next((snmp_column_value.value for snmp_column_value in column_values if snmp_column_value.oid == '5835.5.2.3200.1.2.1.2.'), 0)
        if modem_id != 0:
            channel_stats_parsed[modem_id] = column_values
        
    logged_on_terminals = 0

    for key, column_values in service_stats_result.iteritems():
        modem_id = ntc_netsnmp_tools.decode_octet_string(key)
        channel_stats = []
        if modem_id in channel_stats_parsed:
            channel_stats = channel_stats_parsed[modem_id]

        tags = { 'hps': satnet_if, 'modem_id': modem_id }
        
        #construct fields dictionary from columns in service stats and channel stats. Discard any values 'NA'
        fields = {}
        for column_value in column_values:
            if column_value.value != 'NA':
                key = snmp_service_stats_columns[column_value.oid]
                try:
                    if key == 'ESN0':
                        fields[key] = float(column_value.value) / 100.0
                    elif key == 'rx_level':
                        fields[key] = float(column_value.value) / 10.0
                    elif key == 'tx_power':
                        fields[key] = float(column_value.value) / 10.0
                    else:
                        fields[key] = column_value.value
                except ValueError:
                    fields[key] = float(column_value.value)
        
        if len(channel_stats) > 0:
            for column_value in channel_stats:
                if column_value.value != 'NA':
                    key = snmp_channel_stats_columns[column_value.oid]
                    if key != 'modem_id':#the modem_id column can be discarded, modem_id is already a tag value
                        if key == 'link_margin' and '>' in str(column_value.value):#special handling for link_margin value => value can be '>30' which is a special case, the value shall be replaced by 30
                            fields[key] = 30
                        elif (key == 'C0N' or key == 'C0ND' or key == 'C0D') and '>' in str(column_value.value):
                            fields[key] = float(str(column_value.value)[1:])
                        else:
                            fields[key] = column_value.value
        if 'state' in fields:#keep count of logged on terminals
            state = int(fields['state'])
            if state == 0:
                logged_on_terminals = logged_on_terminals + 1

        yield TMetric(series_name, tm, tags, fields)

    provisioned_terminals = len(channel_stats_parsed)
    yield TMetric('return.S2', tm, { 'hps':satnet_if }, { 'provisioned_terminals': provisioned_terminals, 'logged_on_terminals': logged_on_terminals })


if __name__ == "__main__":
    default_config = {
        ntc_tools.ntc_active_if_name(): ntc_tools.ntc_active_if(),
        }
    default_port = 161
    ntc_main.main(default_config, default_port, register, read, "s2_stats")