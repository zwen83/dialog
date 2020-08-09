#DIALOG VERSION: 2.1.3

import time
from socketmetricscollector import SocketMetricsCollector
from telegrafpy import TMetric

def get(collector, ip_address, port, satnet_if,ptpLayer2VcId , terminal_provisioning_data, terminal_commands_tobuild, type, tm):
    if len(terminal_commands_tobuild) == 0:
        return
        yield

    terminal_commands = []
    terminal_commands.extend([terminal_command.format(type) for terminal_command in terminal_commands_tobuild])

    metrics = collector.execute(ip_address, port, terminal_commands);
  
    #dic to store the metrics
    terminal_single_metrics = dict([(str.format('{0}_{1}',terminal_data[0],terminal_data[1]), []) for terminal_data in terminal_provisioning_data])
    for metric in metrics:
        split_meta_data = str(metric.meta_data).split('_')
        terminal_p2pvcoonection_id = split_meta_data[1] + '_' + split_meta_data[2 ]
        if len(terminal_p2pvcoonection_id) >2:
            terminal_single_metrics[terminal_p2pvcoonection_id].append(metric)

    fwd_name = 'modem.p2p_layer2_vc'

    metrics_counter = 0
    for key,values in terminal_single_metrics.iteritems():
        terminalId_p2pvconnectionId = str(key).split('_')
        terminalId = terminalId_p2pvconnectionId[0]
        p2pvcoonectionId = terminalId_p2pvconnectionId[1]
        tags = { 'hps': satnet_if, 'modem_id' :terminalId , 'ptp_layer2_vc_id': p2pvcoonectionId }
        tmetric_values = dict([(metric.key, metric.value) for metric in values ])
        if len(tmetric_values) > 0:
            metrics_counter += 1
            yield TMetric(fwd_name, tm, tags, tmetric_values)
    
   