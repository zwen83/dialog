#DIALOG VERSION: 2.2.2
import requests
import json
import unicodedata
from telegrafpy import TMetric
import time
import ntc_tools
import ntc_main


class OperationalState():
    Unknown = 0
    Idle = 1
    Waiting = 2
    LoggingOn = 3
    Acquiring = 4
    Syncing = 5
    LoggedOn = 6
    Scheduling = 7
    LogOnFailed = 8
    Stopping = 9
    WaitingULogon = 10
    
class RegrowthLimited():
    NotApplicable = 0
    True = 1
    False = 2
    Indeterminate = 3

def get_regrowth_limited(regrowth_limited):
    states = { 'NotApplicable': RegrowthLimited.NotApplicable, 'true': RegrowthLimited.True, 'false': RegrowthLimited.False, 'Indeterminate': RegrowthLimited.Indeterminate }

    if regrowth_limited != None and regrowth_limited in states.keys():
        return states[regrowth_limited]

    return RegrowthLimited.NotApplicable

def get_modem_qos(shaping_node_name):
    if "_bidir_circuit_" in shaping_node_name:
        modem_id = shaping_node_name[shaping_node_name.rfind('_') + 1:]
        split = shaping_node_name.split('_')
        qos = split[len(split) - 2]
        return (modem_id, qos)

    return ('', '')


def get_terminal_operational_state(terminal_state):
    states = { 'unknown' : OperationalState.Unknown, 'idle' : OperationalState.Idle, 'waiting': OperationalState.Waiting, 'loggingon': OperationalState.LoggingOn
              , 'acquiring': OperationalState.Acquiring, 'syncing': OperationalState.Syncing, 'loggedon' : OperationalState.LoggedOn, 'scheduling': OperationalState.Scheduling
              , 'stopping': OperationalState.Stopping, 'logonfailed': OperationalState.LogOnFailed, 'waitingulogon': OperationalState.WaitingULogon }

    if terminal_state != None and terminal_state.lower() in states.keys():
        return states[terminal_state.lower()]
    
    return OperationalState.Unknown

satnet_if = 0
ntc_active_if_modified = 0
ntc_active_if_file_name = ''
provisioned_terminals_modified = 0
provisioned_terminals_file_name = ''
terminal_ids = []
rtn_qos_classes = ['circuit', 'BE', 'RT1', 'RT2', 'RT3', 'CD1', 'CD2', 'CD3']

def register(config):
    global ntc_active_if_file_name
    global provisioned_terminals_file_name

    module_name = 'hrcctl'

    ntc_active_if_file_name = ntc_tools.get_config(config, module_name, ntc_tools.ntc_active_if_name())
    provisioned_terminals_file_name = ntc_tools.get_config(config, module_name, ntc_tools.terminals_name())

def initialize():
    pass

def read(args):
    global satnet_if
    global ntc_active_if_modified
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
        active_if_changed = True

    #check if terminals file was changed
    if provisioned_terminals_file_name != '':
        (file_modified, modified_date) = ntc_tools.file_has_changed(provisioned_terminals_file_name, provisioned_terminals_modified, active_hps=satnet_if)
        if file_modified or active_if_changed:
            terminal_ids = []
            #re-set modified date for next run
            provisioned_terminals_modified = modified_date
            content = ntc_tools.read_lines(provisioned_terminals_file_name, active_hps=satnet_if)
            terminal_provisioning_data = [x.strip().split('|') for x in content]
            terminal_ids = [terminal_data[0] for terminal_data in  terminal_provisioning_data]
            
    series_name = 'modem.return.hrc_generic'

    statistics_url = ntc_tools.hrcctl_local_url(args.src_host, args.src_port, satnet_if, 'hrccontroller/statistics')
    statistics_response = requests.get(statistics_url)
    
    if statistics_response.status_code == 200:
        jsrsp = statistics_response.json()
        if jsrsp == None:
            return
            yield

        if 'carrierGroups' in jsrsp.keys():
            for carrier_group in jsrsp['carrierGroups']:
                carrier_group_data = jsrsp['carrierGroups'][carrier_group]
                carrier_group_name = carrier_group_data['name'].encode('utf-8')
                split_name = carrier_group_name.split('_')
                rcg_id = split_name[-1]
                rcg_type = split_name[1]
                
                if 'terminals' in jsrsp['carrierGroups'][carrier_group].keys():
                    for terminal in jsrsp['carrierGroups'][carrier_group]['terminals']:
                        trm_data = jsrsp['carrierGroups'][carrier_group]['terminals'][terminal]
                        if not trm_data is None:
                            modem_name = trm_data['name'].encode('utf-8')
                            modem_id = modem_name.split('_')[1]

                            #stop processing if the modem is not provisioned
                            if not modem_id in terminal_ids:
                                continue

                            tags = { 'hps': satnet_if, 'modem_id': modem_id, 'return_capacity_group_id': rcg_id, 'type' : rcg_type }

                            values = {}

                            try:
                                assigned_mcd_role = trm_data['receiveInfo']['assignedMcd']
                                if assigned_mcd_role != None:
                                    values['assigned_mcd_role'] = '"{0}"'.format(assigned_mcd_role.encode('utf-8'))
                            except:
                                pass                                

                            try:
                                state = trm_data['state']
                                if state != None:
                                    values['state'] = get_terminal_operational_state(str(state).encode('utf-8'))
                            except:
                                pass

                            try:
                                chip_rate = trm_data['chipRate']
                                if chip_rate != None:
                                    values['chip_rate'] = chip_rate
                            except:
                                pass

                            try:
                                esno = trm_data['receiveInfo']['esNo']['value']
                                if esno != None:
                                    values['ESN0'] = esno
                            except:
                                pass

                            try:
                                rx_power = trm_data['receiveInfo']['rxPower']['value']
                                if rx_power != None:
                                    values['rx_power'] = rx_power
                            except:
                                pass

                            try:
                                rx_power_density = trm_data['receiveInfo']['rxPowerDensity']['value']
                                if rx_power_density != None:
                                    values['rx_power_density'] = rx_power_density
                            except:
                                pass

                            try:
                                frequency = trm_data['frequency']['value']
                                if frequency != None:
                                    values['frequency'] = frequency
                            except:
                                pass

                            try:
                                frequency_offset = trm_data['frequencyOffset']['value']
                                if frequency_offset != None:
                                    values['frequency_offset'] = frequency_offset
                            except:
                                pass

                            try:
                                bbp_count = trm_data['receiveInfo']['packetCount']
                                if bbp_count != None:
                                    values['bbp_count'] = bbp_count
                            except:
                                pass

                            try:
                                bbp_error_count = trm_data['receiveInfo']['errorPacketCount']
                                if bbp_error_count != None:
                                    values['bbp_error_count'] = bbp_error_count
                            except:
                                pass

                            try:
                                errored_seconds_count = trm_data['erroredSeconds']
                                if errored_seconds_count != None:
                                    values['errored_seconds_count'] = errored_seconds_count
                            except:
                                pass
                    
                            try:
                                allocated_bit_rate = trm_data['bitrate']['value']
                                if allocated_bit_rate != None:
                                    values['allocated_bit_rate'] = allocated_bit_rate
                            except:
                                pass

                            try:
                                tx_power = trm_data['txPower']['value']
                                if tx_power != None:
                                    values['tx_power'] = tx_power
                            except:
                                pass
            
                            try:
                                regrowth_limited_power = trm_data['regrowthLimitedPower']
                                if regrowth_limited_power != None:
                                    values['regrowth_limited_power'] = get_regrowth_limited(regrowth_limited_power.encode('utf-8'))
                            except:
                                pass

                            try:
                                tx_power_density = trm_data['txPowerDensity']['value']
                                if tx_power_density != None: 
                                    values['tx_power_density'] = tx_power_density
                            except:
                                pass

                            try:
                                modcod = trm_data['modcod']
                                if modcod != None:
                                    values['modcod'] = modcod
                            except:
                                pass
            
                            try:
                                spread_factor = trm_data['spreadingFactor']
                                if spread_factor != None:
                                    values['spread_factor'] = spread_factor
                            except:
                                pass

                            try:
                                cod = trm_data['receiveInfo']['coD']['value']
                                if cod != None:
                                    values['C0D'] = cod
                            except:
                                pass

                            try:
                                cond = trm_data['receiveInfo']['coND']['value']
                                if cond != None:
                                    values['C0ND'] = cond
                            except:
                                pass

                            try:
                                link_margin = trm_data['receiveInfo']['linkMargin']['value']
                                if link_margin != None:
                                    values['link_margin'] = link_margin
                            except:
                                pass

                            try:
                                acm_margin = trm_data['acmMargin']['value']
                                if acm_margin != None:
                                    values['ACM_margin'] = acm_margin
                            except:
                                pass

                            try:
                                uplink_fade = trm_data['uplinkFade']['value']
                                if uplink_fade != None:
                                    values['uplink_fade'] = uplink_fade
                            except:
                                pass

                            try:
                                out_of_lock_count = trm_data['outOfLockCount']
                                if out_of_lock_count != None:
                                    values['out_of_lock_count'] = out_of_lock_count
                            except:
                                pass
                                
                            try:
                                bbp_efficiency = trm_data['receiveInfo']['bbpEfficiency']['value']
                                if bbp_efficiency != None:
                                    values['bbp_occupation'] = bbp_efficiency
                            except:
                                pass

                            try:
                                BUC_frequency_offset = trm_data['frequencyOffset']['value']
                                if BUC_frequency_offset != None:
                                    values['BUC_frequency_offset'] = BUC_frequency_offset
                            except:
                                pass

                            try:
                                logon_time = trm_data['loggingOnThreshold']
                                if logon_time != None:
                                    values['logon_time'] = logon_time
                            except:
                                pass

                            try:
                                logon_search_range = trm_data['searchRange']
                                if logon_search_range != None:
                                    values['logon_search_range'] = logon_search_range
                            except:
                                pass

                            try:
                                insufficient_carrier_guard_band = trm_data['receiveInfo']['insufficientGuardBand']
                                if insufficient_carrier_guard_band != None:
                                    values['insufficient_carrier_guard_band'] = insufficient_carrier_guard_band
                            except:
                                pass

                            try:
                                logging_on_carrier_guard_band_too_high_count = trm_data['insufficientGuardBandsLoggedOnCount']
                                if logging_on_carrier_guard_band_too_high_count != None:
                                    values['logging_on_carrier_guard_band_too_high_count'] = logging_on_carrier_guard_band_too_high_count
                            except:
                                pass

                            try:
                                received_ulogon_msg_count = trm_data['ulogon']['receivedMsgs']
                                if received_ulogon_msg_count != None:
                                    values['received_ulogon_msg_count'] = received_ulogon_msg_count
                            except:
                                pass

                            try:
                                requested_ulogon_count = trm_data['ulogon']['sentReqs']
                                if requested_ulogon_count != None:
                                    values['requested_ulogon_count'] = requested_ulogon_count
                            except:
                                pass

                            try:
                                actual_bepd = trm_data['actualBEPD']['value']
                                if actual_bepd != None:
                                    values['actual_BEPD'] = actual_bepd
                            except:
                                pass

                            if len(values) > 0:
                                yield TMetric(series_name, tm, tags, values)

                if 'shapingNodes' in jsrsp['carrierGroups'][carrier_group].keys():
                    valid_shaping_nodes = [ shaping_node_name for shaping_node_name in jsrsp['carrierGroups'][carrier_group]['shapingNodes'].keys() if '_bidir_circuit_' in shaping_node_name or '_rcg_' in shaping_node_name or 'sh_node_tb_cg_' in shaping_node_name or 'sh_node_cb_cg_' or carrier_group_name == shaping_node_name or 'sh_node_free_cap_root_' in shaping_node_name ]

                    for shaping_node in valid_shaping_nodes:
                        shaping_node_data = jsrsp['carrierGroups'][carrier_group]['shapingNodes'][shaping_node]
                        shaping_node_name = shaping_node_data['name'].encode('utf-8')

                        (modem_id, qos) = get_modem_qos(shaping_node_name)

                        if modem_id != '' and qos in rtn_qos_classes and modem_id in terminal_ids:
                            tags = tags = { 'hps': satnet_if, 'modem_id': modem_id, 'qos_class_id': qos, 'return_capacity_group_id': rcg_id, 'type' : rcg_type }
                            values = {}

                            try:
                                assigned_volume = shaping_node_data['assignedVolume']['value']
                                if assigned_volume != None:
                                    values['assigned_volume'] = assigned_volume
                            except:
                                pass

                            try:
                                requested_volume = shaping_node_data['requestedVolume']['value']
                                if requested_volume != None:
                                    values['requested_volume'] = requested_volume
                            except:
                                pass

                            if len(values) > 0:
                                yield TMetric('modem.return.hrc_shaping', tm, tags, values)

                        if '_rcg_' in shaping_node_name:
                            tags = { 'hps': satnet_if, 'return_capacity_group_id': rcg_id, 'type' : rcg_type }
                            values = {}

                            try:
                                assigned_volume = shaping_node_data['assignedVolume']['value']
                                if assigned_volume != None:
                                    values['assigned_volume'] = assigned_volume
                            except:
                                pass

                            try:
                                logged_on_terminals = carrier_group_data['loggedOnTerminals']
                                if logged_on_terminals != None:
                                    values['logged_on_terminals'] = logged_on_terminals
                            except:
                                pass

                            try:
                                provisioned_terminals = carrier_group_data['terminals']
                                if provisioned_terminals != None:
                                    values['provisioned_terminals'] = len(provisioned_terminals)
                                else:
                                    values['provisioned_terminals'] = 0
                            except:
                                pass

                            try:
                                available_bandwidth = carrier_group_data['availableBandwidth']
                                if available_bandwidth != None:
                                    values['available_bandwidth'] = available_bandwidth
                            except:
                                pass

                            try:
                                used_bandwidth = carrier_group_data['usedBandwidth']
                                if used_bandwidth != None:
                                    values['used_bandwidth'] = used_bandwidth
                            except:
                                pass

                            try:
                                logon_bandwidth = carrier_group_data['logonBandwidth']
                                if logon_bandwidth != None:
                                    values['logon_bandwidth'] = logon_bandwidth
                            except:
                                pass

                            try:
                                physical_layer_efficiency = carrier_group_data['physicalLayerEfficiency']
                                if physical_layer_efficiency != None:
                                    values['physical_layer_efficiency'] = physical_layer_efficiency
                            except:
                                pass

                            try:
                                best_modcod_efficiency = carrier_group_data['bestModcodEfficiency']
                                if best_modcod_efficiency != None:
                                    values['best_modcod_efficiency'] = best_modcod_efficiency
                            except:
                                pass

                            try:
                                bbp_efficiency = carrier_group_data['bbpEfficiency']
                                if bbp_efficiency != None:
                                    values['bbp_occupation'] = bbp_efficiency
                            except:
                                pass

                            try:
                                requested_ulogon_count = carrier_group_data['ulogon']['sentReqs']
                                if requested_ulogon_count != None:
                                    values['requested_ulogon_count'] = requested_ulogon_count
                            except:
                                pass

                            try:
                                received_ulogon_count = carrier_group_data['ulogon']['receivedMsgs']
                                if received_ulogon_count != None:
                                    values['received_ulogon_count'] = received_ulogon_count
                            except:
                                pass

                            if len(values) > 0:
                                yield TMetric('return.hrc.return_capacity_group', tm, tags, values)

                        if 'sh_node_tb_cg_' in  shaping_node_name or 'sh_node_cb_cg_' in shaping_node_name:
                            tags = { 'hps': satnet_if, 'return_capacity_group_id': rcg_id, 'return_pool_name': shaping_node_name, 'type' : rcg_type }
                            values = {}

                            try:
                                requested_volume = shaping_node_data['requestedVolume']['value']
                                if requested_volume != None:
                                    values['requested_rate'] = requested_volume
                            except:
                                pass

                            try:
                                allocated_rate = shaping_node_data['assignedVolume']['value']
                                if allocated_rate != None:
                                    values['allocated_rate'] = allocated_rate
                            except:
                                pass

                            try:
                                eir_shaping_ratio = shaping_node_data['eirShapingRatio']
                                if eir_shaping_ratio != None:
                                    values['eir_shaping_ratio'] = eir_shaping_ratio
                            except:
                                pass

                            try:
                                cir_congestion = shaping_node_data['cirCongested']
                                if cir_congestion != None:
                                    values['cir_congestion'] = cir_congestion
                            except:
                                pass

                            if len(values):
                                yield TMetric('return.hrc.shaping', tm, tags, values)

                        if carrier_group_name == shaping_node_name:
                            tags = { 'hps': satnet_if, 'return_capacity_group_id': rcg_id, 'return_pool_name': shaping_node_name, 'type' : rcg_type }
                            values = {}

                            try:
                                requested_volume = shaping_node_data['requestedVolume']['value']
                                if requested_volume != None:
                                    values['requested_rate'] = requested_volume
                            except:
                                pass

                            try:
                                allocated_rate = shaping_node_data['assignedVolume']['value']
                                if allocated_rate != None:
                                    values['allocated_rate'] = allocated_rate
                            except:
                                pass

                            if len(values):
                                yield TMetric('return.hrc.shaping', tm, tags, values)

                        if 'sh_node_free_cap_root_' in shaping_node_name:
                            tags = { 'hps': satnet_if, 'return_capacity_group_id': rcg_id, 'return_pool_name': shaping_node_name, 'type' : rcg_type }
                            values = {}

                            try:
                                allocated_rate = shaping_node_data['assignedVolume']['value']
                                if allocated_rate != None:
                                    values['allocated_rate'] = allocated_rate
                            except:
                                pass

                            if len(values):
                                yield TMetric('return.hrc.shaping', tm, tags, values)

        if 'transponders' in jsrsp.keys():
            series_name = 'return.hrc.transponder'
            
            for transponder in jsrsp['transponders']:
                transponder_data = jsrsp['transponders'][transponder]

                transponder_name = None
                try:
                    transponder_name = transponder_data['name']
                except:
                    pass

                translation_frequency_offset_avg = None
                try:
                    translation_frequency_offset_avg = transponder_data['translationFrequencyOffsetAvg']
                except:
                    pass

                transponder_id = -1
                if transponder_name != None:
                    split_transponder_name = transponder_name.split('_')
                    if len(split_transponder_name) == 2:
                        transponder_id = split_transponder_name[-1]
                if transponder_id != -1 and translation_frequency_offset_avg != None:
                    tags = { 'hps': satnet_if, 'transponder_id': transponder_id }                    
                    values = {}
                    values['frequency_offset'] = translation_frequency_offset_avg

                    yield TMetric(series_name, tm, tags, values)

        if 'demodulators' in jsrsp.keys():
            series_name= 'return.hrc.mcd'

            for demod in jsrsp['demodulators']:
                demod_data = jsrsp['demodulators'][demod]
                values = {}
                tags = { 'hps': satnet_if, 'demod_name': demod }

                try:
                    clear_sky_N0 = demod_data['clearSkyNo']
                    if clear_sky_N0 != None:
                        values['clear_sky_N0'] = clear_sky_N0
                except:
                    pass

                try:
                    actual_N0 = demod_data['actualNo']
                    if actual_N0 != None:
                        values['actual_N0'] = actual_N0
                except:
                    pass

                try:
                    average_N0 = demod_data['avgNo']
                    if average_N0 != None:
                        values['average_N0'] = average_N0
                except:
                    pass

                try:
                    min_N0 = demod_data['minNo']
                    if min_N0 != None:
                        values['min_N0'] = min_N0
                except:
                    pass

                try:
                    max_N0 = demod_data['maxNo']
                    if max_N0 != None:
                        values['max_N0'] = max_N0
                except:
                    pass

                try:
                    frequency_max_N0 = demod_data['freqAtMaxNo']
                    if frequency_max_N0 != None:
                        values['frequency_max_N0'] = frequency_max_N0
                except:
                    pass

                try:
                    symbol_rate_N0 = demod_data['symRateAtMaxNo']
                    if symbol_rate_N0 != None:
                        values['symbol_rate_N0'] = symbol_rate_N0
                except:
                    pass

                try:
                    demod_not_responding_count = demod_data['demodNotResponding']
                    if demod_not_responding_count != None:
                        values['demod_not_responding_count'] = demod_not_responding_count
                except:
                    pass

                try:
                    protocol_errors_count = demod_data['protocolErrors']
                    if protocol_errors_count != None:
                        values['protocol_errors_count'] = protocol_errors_count
                except:
                    pass

                if len(values) > 0:
                    yield TMetric(series_name, tm, tags, values)
                
if __name__ == "__main__":
    default_config = { 
        ntc_tools.ntc_active_if_name() : ntc_tools.ntc_active_if(), 
        ntc_tools.terminals_name(): ntc_tools.rtmc_source_location('terminals'), 
        }
    default_port = 80
    ntc_main.main(default_config, default_port, register, read, "hrcctl")