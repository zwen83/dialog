from socketmetricscollector import SocketMetricsCollector
from telegrafpy import TMetric

def get(ip_address, port, satnet_if, interface_commands, type, tm):
    if len(interface_commands) == 0:
        return
        yield

    collector_fwd = SocketMetricsCollector()
    metrics_fwd_collector = collector_fwd.execute(ip_address, port, interface_commands)

    metrics = dict([ (metric.key, metric.value) for metric in metrics_fwd_collector ])
   
    if(len(metrics) == 0):
        return
        yield

    if type == 'fwd':
        yield TMetric('infra.l2.dem', tm, { 'hps': satnet_if, 'port':'external'  }, { 'received_bytes': metrics['received_bytes'], 'received_packets': metrics['received_packets']})
        yield TMetric('infra.l2.dem', tm, { 'hps': satnet_if, 'port':'internal' }, { 'sent_bytes': metrics['sent_bytes'], 'sent_packets': metrics['sent_packets'] })
    elif type == 'rtn':
        yield TMetric('infra.l2.dem', tm, { 'hps': satnet_if, 'port':'internal'  }, { 'received_bytes': metrics['received_bytes'], 'received_packets': metrics['received_packets']})
        yield TMetric('infra.l2.dem', tm, { 'hps': satnet_if, 'port':'external' }, { 'sent_bytes': metrics['sent_bytes'], 'sent_packets': metrics['sent_packets'] })

