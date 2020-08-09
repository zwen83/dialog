#DIALOG VERSION: 2.2.1
from socketmetricscollector import SocketMetricsCollector
from telegrafpy import TMetric

def get(collector, ip_address, port, satnet_if, commands, multicast_provisioning_data, tm):
    if len(commands) == 0:
        return
        yield

    metrics = collector.execute(ip_address, port, commands);

    name = 'modem.return.decap'

    grouped_multicast_data = dict([(multicast_id, TMetric
    (name, tm, { 'hps': satnet_if, 'modem_id' : multicast_provisioning_data[multicast_id] }, { 'multicast_id': long(multicast_id) })) for multicast_id in multicast_provisioning_data.keys()])

    for metric in metrics:
        split_meta_data = str(metric.meta_data).split('_')
        multicast_id = split_meta_data[1]
        grouped_multicast_data[multicast_id].fields['multicast_{0}'.format(metric.key)] = long(metric.value)

    for value in grouped_multicast_data.values():
        if len(value.fields) > 1:
            yield value

'''

config:
  interval: 30
  log: /var/log/rtm-collector/rtm-collector.log
  loglevel: INFO
  host: localhost
  port: 8186
  database: telegraf
  src_host: 127.0.0.1
  src_port: 10210
  mode: RUNONCE
  prov: { 'multicast':'/var/ntc-active-if/rtmc/multicastcircuits', 'ntc-active-if':'/var/run/ntc-active-if', 'rtn_link':'/var/ntc-active-if/rtmc/rtn_link.yaml', 'terminals':'/var/ntc-active-if/rtmc/rtn_terminals'}

'''