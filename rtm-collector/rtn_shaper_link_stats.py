#DIALOG VERSION: 2.2.1
from socketmetricscollector import SocketMetricsCollector
from telegrafpy import TMetric
import rtn_link_tools

type_map = {
    'root': 'global',
    'multicast_traffic': 'multicast',
    'acm_feedback': 'acm_feedback',
    'terminal_management': 'terminal_management'
    }

def get(collector, ip_address, port, satnet_if, rtn_link_provisioning, commands, tm):
    if len(commands) == 0:
        return
        yield

    metrics = collector.execute(ip_address, port, commands)

    node_group = dict([(type_map[node], []) for node in rtn_link_tools.satnet_command_nodes])
    [node_group[type_map[metric.meta_data]].append(metric) for metric in metrics if 'rcg' not in metric.meta_data]

    name = 'return.decapsulator'
    result = []

    global_fields = {}
    unicast_fields = {}
    control_fields = {}
    multicast_fields = {}

    set_fields('global', node_group, global_fields, None, unicast_fields)
    set_fields('multicast', node_group, multicast_fields, None, unicast_fields)
    set_fields('acm_feedback', node_group, None, control_fields, unicast_fields)
    set_fields('terminal_management', node_group, None, control_fields, unicast_fields)

    if len(global_fields) > 0:
        yield TMetric(name, tm, {'hps': satnet_if, 'return_link_id': rtn_link_provisioning['rtn-link-id'], 'type': 'global'}, global_fields)

    if len(unicast_fields) > 0:
        yield TMetric(name, tm, {'hps': satnet_if, 'return_link_id': rtn_link_provisioning['rtn-link-id'], 'type': 'unicast'}, unicast_fields)

    if len(multicast_fields) > 0:
        yield TMetric(name, tm, {'hps': satnet_if, 'return_link_id': rtn_link_provisioning['rtn-link-id'], 'type': 'multicast'}, multicast_fields)

    if len(control_fields) > 0:
        yield TMetric(name, tm, {'hps': satnet_if, 'return_link_id': rtn_link_provisioning['rtn-link-id'], 'type': 'control'}, control_fields)
        
    parser = rtn_link_tools.RtnLinkConfigParser(rtn_link_provisioning)
    rcg_group = dict([(rcg.id, []) for rcg in parser.rtn_link.return_capacity_groups])
    [rcg_group[get_rcg_id_from_node(metric.meta_data)].append(metric) for metric in metrics if 'rcg' in metric.meta_data]

    name = 'return.decapsulator.return_capacity_group'

    for rcg_id, rcg_metrics in rcg_group.iteritems():
        tags = {'hps': satnet_if, 'return_capacity_group_id': rcg_id}
        fields = dict([(metric.key, long(metric.value)) for metric in rcg_metrics])

        if len(fields) > 0:
            yield TMetric(name, tm, tags, fields)

def set_fields(node_name, node_group, set_in, add_to, subtract_from):
    if node_name in node_group:
        for metric in node_group[node_name]:
            metric_value = long(metric.value)

            if set_in != None:
                set_in[metric.key] = metric_value
            
            if add_to != None:
                if metric.key in add_to:
                    add_to_value = add_to[metric.key]
                    add_to_value = add_to_value + metric_value
                    add_to[metric.key] = add_to_value
                else:
                    add_to[metric.key] = metric_value

            if subtract_from != None:
                if metric.key in subtract_from:
                    subtract_from_value = subtract_from[metric.key]
                    subtract_from_value = subtract_from_value - metric_value
                    subtract_from[metric.key] = subtract_from_value
                else:
                    subtract_from[metric.key] = metric_value

def get_rcg_id_from_node(node):
    split = node.split('_')
    return int(split[-1])
    