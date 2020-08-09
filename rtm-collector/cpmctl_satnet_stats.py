#DIALOG VERSION: 2.2.1
import requests
import json
from telegrafpy import TMetric
import time
import re

def get(amp_stats_url, counter_stats_url, slotpoolcontainer_url, carrierpools_url, rtcarrier_url, shapingnode_url, satnet_if, amp_instance_id, multicast_data, terminal_ids, tm):
    shapingnode_stats_response = requests.get(shapingnode_url)
    amp_stats_response = requests.get(amp_stats_url)
    counter_stats_response = requests.get(counter_stats_url)
    slotpoolcontainer_response = requests.get(slotpoolcontainer_url)
    carrierpools_response = requests.get(carrierpools_url)
    rtcarrier_response = requests.get(rtcarrier_url)

    shaping_node_rcg_data = {}

    if shapingnode_stats_response.status_code == 200:
        jsrsp = shapingnode_stats_response.json()
        if 'shapingnodes' in jsrsp.keys():
            for shapingnode in jsrsp['shapingnodes']:
                shaping_node_desc = str(shapingnode['shaping_node_desc'])
                if shaping_node_desc.startswith('modem_'):
                    res = re.search('modem_(.*)-(.*)', str(shapingnode['shaping_node_desc']))

                    if res != None:
                        terminal_id = res.group(1)

                        #break if terminal is not provisioned
                        if int(terminal_id) in terminal_ids:
                            qos_class = res.group(2)
                            tags = { 'hps': satnet_if, 'modem_id': terminal_id, 'traffic_type': 'unicast', 'qos_class_id': qos_class, 'cpm_controller_id': amp_instance_id } 
                            values = {}

                            outstanding_volume_avg_value = shapingnode['Outstanding_volume_avg']
                            values['outstanding_volume'] = outstanding_volume_avg_value

                            requested_rate_avg_value = shapingnode['Requested_rate_avg']
                            values['requested_rate'] = requested_rate_avg_value

                            assigned_peak_rate_avg_value = shapingnode['Assigned_peak_rate_avg']
                            values['assigned_rate']  = assigned_peak_rate_avg_value

                            yield TMetric("modem.return.cpm_shaping", tm, tags, values)

                if shaping_node_desc.startswith('multicast'):
                    multicast_id = shaping_node_desc.split('_')[2].split('-')[0]
                    if multicast_id in multicast_data:
                        terminal_id = multicast_data[multicast_id]

                        if int(terminal_id) in terminal_ids:
                            tags = { 'hps': satnet_if, 'modem_id': terminal_id, 'traffic_type': 'multicast', 'cpm_controller_id': amp_instance_id } 

                            requested_rate_avg_value = shapingnode['Requested_rate_avg']
                            values['requested_rate'] = requested_rate_avg_value

                            assigned_peak_rate_avg_value = shapingnode['Assigned_peak_rate_avg']
                            values['assigned_rate']  = assigned_peak_rate_avg_value

                            yield TMetric("modem.return.cpm_shaping", tm, tags, values)

                if shaping_node_desc.startswith('returnpool_'):
                    return_capacity_group_id = shapingnode['spc_id']

                    tags = { 'hps': satnet_if, 'cpm_controller_id': amp_instance_id, 'return_capacity_group_id': return_capacity_group_id, 'return_pool_name': shaping_node_desc } 
                    values = {}

                    requested_rate = shapingnode['Requested_rate_avg']
                    values['requested_rate'] = requested_rate

                    allocated_rate = shapingnode['Assigned_peak_rate_avg']
                    values['allocated_rate'] = allocated_rate

                    eir_shaping_ratio = shapingnode['wcr_avg']
                    values['eir_shaping_ratio'] = eir_shaping_ratio

                    cir_congestion= shapingnode['Cir_congestion']
                    values['cir_congestion'] = cir_congestion

                    yield TMetric('return.cpm.shaping', tm, tags, values)

                if shaping_node_desc.startswith('returncapacitygroup_'):
                    return_capacity_group_id = shapingnode['spc_id']
                    shaping_node_rcg_data[return_capacity_group_id] = shapingnode

    tags = {'hps': satnet_if, 'cpm_controller_id': amp_instance_id}
    values = {}

    if amp_stats_response.status_code == 200:
        amp_stats_json = amp_stats_response.json()
        nbr_provisioning_terminals = amp_stats_json['prov_sits']
        values['nbr_provisioned_terminals'] = nbr_provisioning_terminals

        nbr_operational_terminals = amp_stats_json['Loggedon_sits']
        values['nbr_operational_terminals'] = nbr_operational_terminals

        window_used = amp_stats_json['window_used']
        values['window_used']  = window_used

        time_offset_rx_bursts = amp_stats_json['deltaT_with_BDM']
        values['time_offset_rx_bursts'] = time_offset_rx_bursts

        spot_frequency_offset = amp_stats_json['spot_deltaF']
        values['spot_frequency_offset'] = spot_frequency_offset

        spot_time_offset = amp_stats_json['spot_deltaT']
        values['spot_time_offset'] = spot_time_offset

    if counter_stats_response.status_code == 200:
        counter_stats_json = counter_stats_response.json()

        if 'total_ok_slots' in counter_stats_json:
            slots_ok_burst = counter_stats_json['total_ok_slots']
            values['slots_ok_burst'] = slots_ok_burst

        if 'total_missed_slots' in counter_stats_json:
            slots_errored_burst = counter_stats_json['total_missed_slots']
            values['slots_errored_burst'] = slots_errored_burst

        if 'slots_not_bursted_on' in counter_stats_json:
            slots_not_bursted_on = counter_stats_json['slots_not_bursted_on']
            values['slots_not_bursted_on'] = slots_not_bursted_on
        
    yield TMetric('return.cpm', tm, tags, values)

    if slotpoolcontainer_response.status_code == 200:
        slotpoolcontainer_json = slotpoolcontainer_response.json()

        for slotpoolcontainer in slotpoolcontainer_json['slotpoolcontainers']:
            return_capacity_group_id = slotpoolcontainer['spc_id']
            tags = {'hps': satnet_if, 'cpm_controller_id': amp_instance_id, 'return_capacity_group_id': return_capacity_group_id}
            values = {}

            provisioned_terminals = slotpoolcontainer['provisioned_sit_avg']
            values['provisioned_terminals'] = provisioned_terminals

            logged_in_terminals = slotpoolcontainer['loggedon_sit_avg']
            values['logged_in_terminals'] = logged_in_terminals

            logons_average = slotpoolcontainer['sit_logons_avg']
            values['logons_average'] = logons_average

            idle_logoffs_average = slotpoolcontainer['idle_logoffs_avg']
            values['idle_logoffs_average'] = idle_logoffs_average

            error_logoff_average = slotpoolcontainer['order_logoffs_avg']
            values['error_logoff_average'] = error_logoff_average

            slots_idle_volume = slotpoolcontainer['idle_vol_avg']
            values['slots_idle_volume'] = slots_idle_volume

            slots_busy_volume = slotpoolcontainer['busy_vol_avg']
            values['slots_busy_volume'] = slots_busy_volume

            slots_busy_volume_div = slots_busy_volume + slots_idle_volume
            if slots_busy_volume_div != 0:
                values['burst_packet_occupation'] = float(slots_busy_volume / (slots_busy_volume + slots_idle_volume))

            rx_lost_volume_average = slotpoolcontainer['lost_vol_avg']
            values['slots_lost_volume'] = rx_lost_volume_average

            schedule_duration = slotpoolcontainer['schedule_duration_avg']
            values['schedule_duration'] = schedule_duration

            if return_capacity_group_id in shaping_node_rcg_data:
                shaping_node_data = shaping_node_rcg_data[return_capacity_group_id]
                
                requested_rate = shaping_node_data['Requested_rate_avg']
                values['requested_rate'] = requested_rate

                allocated_rate = shaping_node_data['Assigned_peak_rate_avg']
                values['allocated_rate'] = allocated_rate

            yield TMetric('return.cpm.return_capacity_group', tm, tags, values)

    if carrierpools_response.status_code == 200:
        carrierpools_json = carrierpools_response.json()

        for carrierpool in carrierpools_json['carrierpools']:
            tags = { 'hps': satnet_if, 'cpm_controller_id': amp_instance_id, 'carrier_pool_id': carrierpool['cp_id'] } 
            values = {}

            number_terminals = carrierpool['scheduled_sit_avg']
            values['number_terminals'] = number_terminals

            scheduled_cir = carrierpool['cir_load_avg']
            values['scheduled_cir'] = scheduled_cir

            scheduled_EIR = carrierpool['eir_load_avg']
            values['scheduled_EIR'] = scheduled_EIR

            yield TMetric('return.cpm.return_carrier_pool', tm, tags, values)

    if rtcarrier_response.status_code == 200:
        rtcarrier_json = rtcarrier_response.json()

        for rtcarrier in rtcarrier_json['rtcarriers']:            
            tags = { 'hps': satnet_if, 'cpm_controller_id': amp_instance_id, 'carrier_id': rtcarrier['carrier_id'] } 
            values = {}

            valid_bursts = rtcarrier['nbr_TRF_bursts_avg']
            values['valid_bursts'] = valid_bursts

            errored_bursts = rtcarrier['missed_slots_avg']
            values['errored_bursts'] = errored_bursts

            CN0_average = rtcarrier['CNo_avg']
            values['CN0_average'] = CN0_average

            C0_average = rtcarrier['C0_avg']
            values['C0_average'] = C0_average

            C0_min = rtcarrier['C0_min']
            values['C0_min'] = C0_min

            C0_max = rtcarrier['C0_max']
            values['C0_max'] = C0_max

            csc_bursts = rtcarrier['nbr_CSC_bursts_avg']
            values['CSC_bursts'] = csc_bursts

            yield TMetric('return.cpm.return_carrier', tm, tags, values)