#DIALOG VERSION: 2.2.2
import ntc_tools
import time
from itertools import chain
import logging
import ntc_daemon
import requests
import json
from telegrafpy import TMetric
from datetime import datetime
import ntc_main

satnet_if = 0

provisioned_terminals_file_name = ''
provisioned_terminals_modified = 0

terminal_ids = []

def register(config):
    global satnet_if
    global provisioned_terminals_file_name

    module_name = 'tcs_stats'

    #for lack of a ntc-active-if file on the TCS virtual machine. The active IF number is injected into the ntc-active-if key
    satnet_if = ntc_tools.get_config(config, module_name, ntc_tools.ntc_active_if_name())
    provisioned_terminals_file_name = ntc_tools.get_config(config, module_name, ntc_tools.terminals_name())

def initialize():
    pass

def read(args):
    global satnet_if
    global provisioned_terminals_modified
    global terminal_ids
    
    tm = ntc_tools.get_polling_time(args.interval)

    #check if '/var/ntc-active-if' has changed (first run, this will always be the case) => obsolete in this case, since satnet_if is injected directly in the input config of the script
    
    #check if terminals file was changed
    if provisioned_terminals_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(provisioned_terminals_file_name, provisioned_terminals_modified)
        if file_modified:
            #re-set modified date for next run
            provisioned_terminals_modified = modified_date
            content = ntc_tools.read_lines(provisioned_terminals_file_name, active_hps=satnet_if)
            terminal_provisioning_data = [x.strip().split('|') for x in content]
            terminal_ids = [int(terminal_data[0]) for terminal_data in terminal_provisioning_data]
    

    if len(terminal_ids) == 0:
        return
        yield

    tcs_url = ntc_tools.tcs_local_url(args.src_host, args.src_port, satnet_if, 'tcs/rest/status/all')
    tcs_response = requests.get(tcs_url)

    if tcs_response.status_code == 200:
        tcs_json = tcs_response.json()
        epoch = datetime.utcfromtimestamp(0)

        for tcs_terminal_data in tcs_json:
            modem_id = tcs_terminal_data.get('terminalId')
            tags = { 'hps': satnet_if, 'modem_id': modem_id }
            values = {}

            network_config_version = tcs_terminal_data.get('networkConfigurationVersion')
            if network_config_version != None:
                values['network_config_version'] = '"{0}"'.format(network_config_version)

            sw_version = tcs_terminal_data.get('terminalSoftwareVersion')
            if sw_version != None:
                values['sw_version'] = '"{0}"'.format(sw_version)

            time_last_network_config = tcs_terminal_data.get('lastDownloadedNetworkConfiguration')
            if time_last_network_config != None:
                dt_time_last_network_config = datetime.strptime(time_last_network_config, '%Y-%m-%dT%H:%M:%S.%f')
                values['time_last_network_config'] = ntc_tools.get_total_seconds(dt_time_last_network_config - epoch)
            satellite_configuration_version = tcs_terminal_data.get('satelliteConfigurationVersion')
            if satellite_configuration_version != None:
                values['satellite_configuration_version'] = satellite_configuration_version
                tags['satellite_configuration_version'] = satellite_configuration_version
            last_downloaded_satellite_configuration_time = tcs_terminal_data.get('lastDownloadedSatelliteConfigurationTime')
            if last_downloaded_satellite_configuration_time != None:
                dt_time_last_satellite_config = datetime.strptime(last_downloaded_satellite_configuration_time, '%Y-%m-%dT%H:%M:%S.%f')
                values['last_downloaded_satellite_configuration_time'] = ntc_tools.get_total_seconds(dt_time_last_satellite_config - epoch)
            required_satellite_configuration_version = tcs_terminal_data.get('requiredSatelliteConfigurationVersion')
            if required_satellite_configuration_version != None:
                values['required_satellite_configuration_version'] = required_satellite_configuration_version
                tags['required_satellite_configuration_version'] = required_satellite_configuration_version
            candidate_satellite_configuration_version = tcs_terminal_data.get("candidateSatelliteConfigurationVersion")
            if candidate_satellite_configuration_version != None:
                values['candidate_satellite_configuration_version'] = candidate_satellite_configuration_version
                tags['candidate_satellite_configuration_version'] = candidate_satellite_configuration_version

            if len(values) > 0:
                yield TMetric('modem.tcs', tm, tags, values)


if __name__ == "__main__":
    default_config = { 
        ntc_tools.ntc_active_if_name(): 1, 
        ntc_tools.bdm_roles_name() : ntc_tools.bdm_roles(), 
        ntc_tools.multicast_name(): ntc_tools.rtmc_source_location('multicastcircuits'), 
        ntc_tools.terminals_name(): ntc_tools.rtmc_source_location('terminals'),
        }
    default_port = 80
    ntc_main.main(default_config, default_port, register, read, "tcs_stats")