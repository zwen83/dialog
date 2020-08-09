#DIALOG VERSION: 2.2.2
import requests
import json
from telegrafpy import TMetric
import time
import ntc_tools
from multiprocessing.dummy import Pool
import re
import logging
import ntc_daemon
from functools  import partial
import ntc_main

terminal_info = []
rtm_terminals_modified = 0
ntc_active_if_modified = 0
satnet_if = 0
tm = 0
ntc_active_if_file_name = ''
rtm_terminals_file_name = ''

class terminalinfo:
    def __init__(self, system_id, remote_gui_url):
        self.system_id = system_id
        self.remote_gui_url = remote_gui_url

def register(config):
    global ntc_active_if_file_name
    global rtm_terminals_file_name

    module_name = 'remote_terminal_monitoring'

    ntc_active_if_file_name = ntc_tools.get_config(config, module_name, ntc_tools.ntc_active_if_name())
    rtm_terminals_file_name = ntc_tools.get_config(config, module_name, ntc_tools.rtm_terminals_name())

def initialize():
    pass

def read(args):
    global rtm_terminals_modified
    global ntc_active_if_modified
    global terminal_info
    global satnet_if
    global tm
    active_if_changed = False

    tm = time.time()
    #check if '/var/ntc-active-hps' has changed (first run, this will always be the case)
    (file_modified, modified_date) = ntc_tools.file_has_changed(ntc_active_if_file_name, ntc_active_if_modified)
    if file_modified:
        #re-set modifief date for next run
        ntc_active_if_modified = modified_date
        satnet_if = ntc_tools.read_single_line(ntc_active_if_file_name)
        active_if_changed = True
    
    (file_modified, modified_date) = ntc_tools.file_has_changed(rtm_terminals_file_name, rtm_terminals_modified, active_hps=satnet_if)
    if file_modified or active_if_changed:
        rtm_terminals_modified = modified_date
        terminal_info = []
        content = ntc_tools.read_lines(rtm_terminals_file_name, active_hps=satnet_if)
        for line in content:
            splits = line.strip().split('|')
            terminal_id = splits[0]
            remote_gui_url = splits[1]
            info = terminalinfo(terminal_id, remote_gui_url)
            terminal_info.append(info)

    return execute_parallel(args)


def make_the_call(info, args):
    url = ntc_tools.tcs_local_url(args.src_host, args.src_port, info)
    response = requests.get(url)

    if response.status_code == 200:
        metrics = []
        jsrsp = response.json()            
        request_data = jsrsp['RequestData']
        values = {}

        #general device status
        status= request_data['Status']
        cpu_usage = status['CpuUsage']
        for index, value in enumerate(cpu_usage):
            values['core.{0}'.format(index)] = value
        values['temp'] = status['Temp']
        if status['TempState'] == None:
            values['temp_state'] = "Not Available"
        else:
            values['temp_state'] = status['TempState']

        system = request_data['System']
        values['up_time'] = system['UpTime'] * 10
            
        #event counters
        modem_event = request_data['Events']
        values['fast_syncs'] = modem_event['FastSyncs']
        values['fw_errs'] = modem_event['FwErrs']
        values['full_reinits'] = modem_event['FullReinits']
        values['nrc_not_recvds'] = modem_event['NcrNotRecvds']
        values['nrc_wrongs'] = modem_event['NcrWrongs']
        values['ncr_lates'] = modem_event['NcrLates']
        values['l3_cfg_fails'] = modem_event['L3CfgFails']
        values['rt_errs'] = modem_event['RtErrs']
        values['opers'] = modem_event['Opers']
        values['syncs'] = modem_event['Syncs']

        #demod stats
        if "Demod" in request_data:
            demod = request_data["Demod"]

        if demod == None and "Demods" in request_data:
            demod_select = [x for x in request_data['Demods'] if x['DemodId'] == 0]
            if len(demod_select) > 0:
                demod = demod_select[0]

        if demod != None:                
            values['demod_locks'] = demod['Locks']
            values['demod_rx_pwr'] = demod['RxPwr']
            values['demod_es_no'] = demod['EsN0']
            values['demod_rx_freq'] = demod['RxFreq']
            values['demod_rx_symbol_rate'] = demod['RxSymRate']
            values['demod_phy_frms'] = demod['PhyFrms']
            values['demod_dmmy_frms'] = demod['DmmyFrms']
            values['demod_bbd_frms'] = demod['BbdFrms']
            values['demod_modcod'] = demod['Modcod']

        metrics.append(TMetric('modem', tm, { 'role': satnet_if, 'modem' : info.system_id, 'type': 'rtm' }, values))

        #modcod related stats
        if 'ModCods' in demod:
            modcods = demod['ModCods']
            if type(modcods) is dict:
                for modcod_id, modcod in modcods.iteritems():
                    modcod_values = {}
                    modcod_values['bbd_frms'] = modcod['BbdFrms']
                    modcod_values['bbd_drp_frms'] = modcod['BbdDrpFrms']

                    metrics.append(TMetric('modem', tm, { 'role': satnet_if, 'modem' : info.system_id, 'type': 'rtm', 'modcod': modcod['Id'] }, modcod_values))
            elif type(modcods) is list:
                for modcod in modcods:
                    modcod_values = {}
                    modcod_values['bbd_frms'] = modcod['BbdFrms']
                    modcod_values['bbd_drp_frms'] = modcod['BbdDrpFrms']

                    metrics.append(TMetric('modem', tm, { 'role': satnet_if, 'modem' : info.system_id, 'type': 'rtm', 'modcod': modcod['Id'] }, modcod_values))


        #qos related statistics
        traffic = request_data['Traffic']

        qos_values = dict([(item['Name'], {}) for item in traffic.values()])

        for index, qos in traffic.iteritems():
            qos_class = qos['Name']
            qos_values[qos_class]['trf_type'] = qos['TrfType']
            qos_values[qos_class]['rt_rx_bytes'] = qos['RtRxBytes']
            qos_values[qos_class]['rt_tx_bytes'] = qos['RtTxBytes']
            qos_values[qos_class]['rt_tx_bitrate'] = qos['RtTxBitrate']
            qos_values[qos_class]['rt_drop_pkts'] = qos['RtDropPkts']
            qos_values[qos_class]['rt_drop_bytes'] = qos['RtDropBytes']
            qos_values[qos_class]['rt_drop_bitrate'] = qos['RtDropBitrate']
            qos_values[qos_class]['rt_queue_time'] = qos['RtQueueTime']

        tcp_info = request_data['TcpSess']
        for tcp_name, sess in tcp_info.iteritems():
            qos_class = sess['Name']
            qos_values[qos_class]['tcp_sess'] = sess['TcpSess']
            qos_values[qos_class]['tcp_sess_lan'] = sess['TcpSessLan']
            qos_values[qos_class]['tcp_sess_hub'] = sess['TcpSessHub']
            qos_values[qos_class]['tcp_dess_dest'] = sess['TcpSessDest']

        for qos_class in qos_values.keys():
            metrics.append(TMetric('modem', tm, { 'role': satnet_if, 'modem' : info.system_id, 'type': 'rtm', 'qos_class': qos_class }, qos_values[qos_class]))

        return metrics

def execute_parallel(args, threads = 100):
    pool = Pool(threads)
    make_the_call_partial = partial(make_the_call, args=args)
    results = pool.map(make_the_call_partial, terminal_info)
    pool.close()
    pool.join()

    flat_results = (result for sub_result in results for result in sub_result)
    return flat_results


if __name__ == "__main__":
    default_config = { 
        ntc_tools.ntc_active_if_name(): ntc_tools.ntc_active_if(), 
        ntc_tools.rtm_terminals_name(): ntc_tools.rtmc_source_location('rtm_terminals'), 
        }
    default_port = 80
    ntc_main.main(default_config, default_port, register, read, "remote_terminal_monitoring")