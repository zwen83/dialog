#DIALOG VERSION: 2.2.2
from socketmetricscollector import SocketMetricsCollector
from telegrafpy import TMetric

def get(collector, ip_address, port, satnet_if, commands, terminal_provisioning_data, tm):
    if len(commands) == 0:
        return
        yield
            
    name = 'modem.return.decap'
    qos_classes = [ 'BE', 'CD1', 'CD2', 'CD3', 'CD4', 'CD5', 'CD6', 'CD7', 'CD8', 'CD9', 'CD10', 'CD11', 'CD12', 'CD13', 'CD14', 'RT1', 'RT2', 'RT3' ]

    metrics = collector.execute(ip_address, port, commands)
    '''
    [<metric.Metric instance at 0x1d6b950>, 
    <metric.Metric instance at 0x1d6b998>, 
    <metric.Metric instance at 0x1d6b9e0>, 
    <metric.Metric instance at 0x1d6ba70>, 
    <metric.Metric instance at 0x1d6bab8>, 
    <metric.Metric instance at 0x1d6bb00>]
    '''

    #group terminals (use metric meta_data field)
    terminal_qos_metrics = dict([(terminal_data[0],
                                  dict([(qos_class,
                                         TMetric(name,
                                                 tm,
                                                 {'hps': satnet_if,
                                                  'modem_id' : terminal_data[0],
                                                  'qos_class_id': qos_class},
                                                 {}))
                                        for qos_class in terminal_data[1:]]))
                                 for terminal_data in terminal_provisioning_data])

    '''
    {'18510': {'BE': 1589017830000000000 modem.return.decap {'hps': '1', 'host': 'PGIDCP-2', 'qos_class_id': 'BE', 'modem_id': '18510'} {}}, 
    '18074': {'BE': 1589017830000000000 modem.return.decap {'hps': '1', 'host': 'PGIDCP-2', 'qos_class_id': 'BE', 'modem_id': '18074'} {}}, 
    '11958': {'BE': 1589017830000000000 modem.return.decap {'hps': '1', 'host': 'PGIDCP-2', 'qos_class_id': 'BE', 'modem_id': '11958'} {}}}
    '''
    for metric in metrics:
        split_meta_data = str(metric.meta_data).split('_')
        modem_id = split_meta_data[1]
        qos_class = split_meta_data[2]
        terminal_qos_metrics[modem_id][qos_class].fields[metric.key] = long(metric.value)

    for qos_values in terminal_qos_metrics.values():
        '''
        qos_values:
        {'BE': 1589017830000000000 modem.return.decap 
        {'hps': '1', 'host': 'PGIDCP-2', 'qos_class_id': 'BE', 'modem_id': '18510'} 
        {'received_bytes': 79198526L, 'received_packets': 227858L}}

        '''

        for value in qos_values.values():
            '''
            value:
            1589017830000000000 modem.return.decap {'hps': '1', 'host': 'PGIDCP-2', 'qos_class_id': 'BE', 'modem_id': '18510'}
             {'received_bytes': 79198526L, 'received_packets': 227858L}
            '''
            if len(value.fields) > 0:

                yield value