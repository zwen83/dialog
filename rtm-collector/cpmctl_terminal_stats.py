#DIALOG VERSION: 2.2.1
import requests
import json
from telegrafpy import TMetric

def get(url, satnet_if, amp_instance_id, terminal_ids, tm):
    series_name = 'modem.return.cpm_generic'
    response = requests.get(url)

    if response.status_code == 200:
        jsrsp = response.json()

        aggregation_interval_start = jsrsp['aggregation_interval_start']
        aggregation_interval_end = jsrsp['aggregation_interval_end']

        if 'sits' in jsrsp.keys():
            for sit in jsrsp['sits']:
                sit_id_value = sit['sit_id']

                #break if terminal is not provisioned
                if not sit_id_value in terminal_ids:
                    continue

                tags = { 'hps': satnet_if, 'modem_id': sit_id_value, 'cpm_controller_id': amp_instance_id }
                values = {}

                sit_state_value = sit['sit_state']
                values['state'] = sit_state_value

                logon_time_value = sit['active_time']
                values['logged_on_time'] = logon_time_value

                terminal_logon_count_value = sit['nof_logons']
                values['log_on_count'] = terminal_logon_count_value

                cno_avg_value = sit['CNo_avg']
                values['CN0_average'] = cno_avg_value

                cno_min_value = sit['CNo_min']
                values['CN0_minimum'] = cno_min_value

                cno_max_value = sit['CNo_max']
                values['CN0_maximum'] = cno_max_value

                carrierpoolid_high_value = sit['carrierpoolid_high']
                values['carrier_pool_high'] = carrierpoolid_high_value

                carrierpoolid_low_value = sit['carrierpoolid_low']
                values['carrier_pool_low'] = carrierpoolid_low_value

                link_margin_avg_value = sit['link_margin_avg']
                values['link_margin_average'] = link_margin_avg_value

                link_margin_min_value = sit['link_margin_min']
                values['link_margin_minimum'] = link_margin_min_value

                link_margin_max_value = sit['link_margin_max']
                values['link_margin_maximum'] = link_margin_max_value

                co_avg_value = sit['C0_avg']
                values['C0_average'] = co_avg_value

                frequency_offset_avg_value = sit['frequency_offset_avg']
                values['frequency_offset_average'] = frequency_offset_avg_value

                frequency_offset_min_value = sit['frequency_offset_min']
                values['frequency_offset_minimum'] = frequency_offset_min_value

                frequency_offset_max_value = sit['frequency_offset_max']
                values['frequency_offset_maximum'] = frequency_offset_max_value

                burst_time_offset_avg_value = sit['time_avg']
                values['burst_time_offset_average'] = burst_time_offset_avg_value

                burst_time_offset_min_value = sit['time_min']
                values['burst_time_offset_minimum'] = burst_time_offset_min_value

                burst_time_offset_max_value = sit['time_max']
                values['burst_time_offset_maximum'] = burst_time_offset_max_value

                busy_vol = float(sit['busy_vol'])
                idle_vol = float(sit['idle_vol'])
                busy_vol_idle_vol = busy_vol + idle_vol
                if busy_vol_idle_vol > 0:
                    burst_packet_efficiency = (busy_vol / busy_vol_idle_vol) * 100.0
                    values['burst_packet_occupation'] = burst_packet_efficiency

                lost_vol = float(sit['lost_vol'])
                lost_vol_busy_vol_idle_vol = lost_vol + busy_vol + idle_vol
                if lost_vol_busy_vol_idle_vol > 0:
                    burst_error_ratio = (lost_vol / lost_vol_busy_vol_idle_vol) * 100.0
                    values['burst_error_ratio'] = burst_error_ratio
            
                if 'assigned_slots' in sit:
                    assigned_slots = float(sit['assigned_slots'])
                    time_interval = aggregation_interval_end - aggregation_interval_start
                    if time_interval > 0:
                        values['assigned_slots'] =  assigned_slots / float(time_interval)
                        values['assigned_bitrate'] = (assigned_slots / float(time_interval)) * 121 * 8

                tx_power_avg = sit['txPower_avg']
                values['tx_power_average'] = tx_power_avg

                tx_power_maximum = sit['txPower_max']
                values['tx_power_maximum'] = tx_power_maximum

                tx_power_minimum = sit['txPower_min']
                values['tx_power_minimum'] = tx_power_minimum

                tx_psd_average = sit['txPsd_avg']
                values['tx_psd_average'] = tx_psd_average

                tx_psd_maximum = sit['txPsd_max']
                values['tx_psd_maximum'] = tx_psd_maximum

                tx_psd_minimum = sit['txPsd_min']
                values['tx_psd_minimum'] = tx_power_avg+tx_psd_minimum

                yield TMetric(series_name, tm, tags, values)