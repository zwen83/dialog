#DIALOG VERSION: 2.2.2
import time
from socketmetricscollector import SocketMetricsCollector
from telegrafpy import TMetric
import logging
import ntc_tools

def get(collector, ip_address, port, satnet_if, terminal_ids, terminal_commands, tm):
    if len(terminal_commands) == 0:
        return
        yield

    qos_classes = [ 'BE', 'CD1', 'CD2', 'CD3', 'CD4', 'CD5', 'CD6', 'CD7', 'CD8', 'CD9', 'CD10', 'CD11', 'CD12', 'CD13', 'CD14', 'RT1', 'RT2', 'RT3' ]
    encap_name = 'modem.forward.encap'
    fwd_name = 'modem.forward.S2'

    metrics = collector.execute(ip_address, port, terminal_commands);    
    
    #group terminals (use metric meta_data field)
    terminal_single_metrics = dict([(terminal_id, TMetric(fwd_name, tm, {'hps':satnet_if, 'modem_id': terminal_id}, {})) for terminal_id in terminal_ids])    
    terminal_qos_metrics = dict([(terminal_id, dict([(qos_class, TMetric(encap_name, tm, { 'hps': satnet_if, 'modem_id' : terminal_id, 'qos_class_id': qos_class }, {})) for qos_class in qos_classes])) for terminal_id in terminal_ids])
    for metric in metrics:
        split_meta_data = str(metric.meta_data).split('_')
        split_modem_id = split_meta_data[ len(split_meta_data) - 1 ].split('-')
        modem_id = split_modem_id[0]
        if len(split_modem_id) == 1:
            if metric.key == 'modcod':
                terminal_single_metrics[modem_id].fields[metric.key] = '"{0}"'.format(' '.join(metric.parts[3:]))
            else:
                terminal_single_metrics[modem_id].fields[metric.key] = float(metric.value)
        else:
            qos_class = split_modem_id[1]
            terminal_qos_metrics[modem_id][qos_class].fields[metric.key] = long(metric.value)
            
    for value in terminal_single_metrics.values():
        if len(value.fields) > 0:
            yield value

    for qos_values in terminal_qos_metrics.values():
        for value in qos_values.values():
            if len(value.fields) > 0:
                yield value