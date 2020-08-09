#DIALOG VERSION: 2.2.1
from telegrafpy import TMetric
from itertools import chain

type_map = {    
    'root': 'root',
    'satnet': 'global',
    'multicast': 'multicast',
    'multicast_sr': 'multicast_sr',
    'control': 'control',
    'control_sr': 'control_sr',
    'management': 'management',
    'management_sr': 'management_sr',
    'trm_ntp': 'control_symbol_rate',
    'trm_sw_upd': 'control_symbol_rate',
    'trm_user_class_1_amp': 'control_symbol_rate',
    'trm_user_class_1_cpm_s2x_hrc': 'control_symbol_rate',
    'trm_user_class_1_ftb': 'control_symbol_rate',
    'trm_user_class_1_hrcctl': 'control_symbol_rate',
    'trm_user_class_1_ncr': 'control_symbol_rate',
    'trm_user_class_1_s2xctl': 'control_symbol_rate',
    'trm_user_class_1_stb': 'control_symbol_rate',
    'trm_user_class_2_cse': 'control_symbol_rate',
    'trm_user_class_2_ftb': 'control_symbol_rate'
    }

field_map = {
    'sent_volume': 'sent_symbols',
    'avg_delay': 'delay',
    'accounting_avg_shaping_ratio': 'eir_shaping_ratio'
    }

def get(collector, ip_address, port, satnet_if, fwd_link_config, peak_rate, tm):
    if fwd_link_config == None or len(fwd_link_config.commands) == 0:
        return chain([])

    metrics = collector.execute(ip_address, port, fwd_link_config.commands)

    global_metrics = [ metric for metric in metrics if 'forwardpool' not in metric.full_metric and 'multicast_' not in metric.full_metric ]
    fwd_pool_metrics = [ metric for metric in metrics if 'forwardpool' in metric.full_metric ]
    hub_multicast_circuit_metrics = [ metric for metric in metrics if 'multicast_' in metric.full_metric ]

    global_series = get_global_series(tm, satnet_if, fwd_link_config, peak_rate, global_metrics)
    fwd_pool_series = get_fwd_pool_series(tm, satnet_if, fwd_link_config, fwd_pool_metrics)
    hub_multicast_circuit_series = get_hub_multicast_circuit(tm, satnet_if, fwd_link_config, hub_multicast_circuit_metrics)

    return chain(global_series, fwd_pool_series, hub_multicast_circuit_series)


def get_global_series(tm, satnet_if, fwd_link_config, peak_rate, global_metrics):
    if fwd_link_config == None or fwd_link_config.fwd_link == None or fwd_link_config.fwd_link.fwd_link_id == None or fwd_link_config.fwd_link.fwd_link_id == 0:
        return
        yield

    name = 'forward.shaper'
    fwd_link_id = fwd_link_config.fwd_link.fwd_link_id

    type_group = dict([(key, []) for key in type_map.values()])
    [type_group[type_map[metric.meta_data]].append(metric) for metric in global_metrics]
    
    global_fields = {}
    unicast_fields = {}
    multicast_fields = {}
    control_fields = {}
    sw_upgrade_fields = {}

    if 'root' in type_group:
        for metric in type_group['root']:
            if metric.key == 'send_rate' and peak_rate != None and peak_rate > 0:
                send_rate = long(metric.value)
                link_occupation = (100 * send_rate) / peak_rate
                global_fields['link_occupation'] = link_occupation
            if metric.key == 'sent_volume':
                sent_volume = long(metric.value)
                global_fields['sent_symbols'] = sent_volume

                if len(type_group['multicast_sr']) > 0 and len(type_group['control_sr']) > 0 and len(type_group['management_sr']) > 0:
                    unicast_fields['sent_symbols'] = sent_volume

    if 'global' in type_group:
        for metric in type_group['global']:
            if metric.key == 'send_rate' and peak_rate != None and peak_rate > 0:
                send_rate = float(metric.value)
                link_efficiency = send_rate / peak_rate
                global_fields['link_efficiency'] = link_efficiency

    if 'control_symbol_rate' in type_group:
        control_symbol_rate = long(0)
        sw_upgrade_symbol_rate = long(0)
        for metric in type_group['control_symbol_rate']:
            control_symbol_rate += long(metric.value)
            if metric.meta_data == 'trm_sw_upd':
                sw_upgrade_symbol_rate +=long(metric.value)

        control_fields['symbol_rate'] = control_symbol_rate
        sw_upgrade_fields['symbol_rate'] = sw_upgrade_symbol_rate
        #control used to have link_occupation as well, check if this is still needed.
        if peak_rate != None and peak_rate > 0:
            control_link_occupation = (control_symbol_rate / peak_rate) * 100.0
            control_fields['link_occupation'] = control_link_occupation

    set_fields(type_group, 'global', global_fields, None, unicast_fields)

    #delete the send_rate
    if 'send_rate' in global_fields:
        del global_fields['send_rate']

    set_fields(type_group, 'multicast', multicast_fields, None, unicast_fields)
    set_fields(type_group, 'multicast_sr', multicast_fields, None, unicast_fields)
    set_fields(type_group, 'control', control_fields, None, unicast_fields)
    set_fields(type_group, 'control_sr', control_fields, None, unicast_fields)
    set_fields(type_group, 'management', sw_upgrade_fields, control_fields, unicast_fields)
    set_fields(type_group, 'management_sr', sw_upgrade_fields, control_fields, unicast_fields)
    
    if len(global_fields) > 0:
        yield TMetric(name, tm, {'hps': satnet_if, 'forward_link_id': fwd_link_id, 'type': 'global'}, global_fields)

    if len(unicast_fields) > 0:
        if 'delay' in unicast_fields:
            del unicast_fields['delay']

        yield TMetric(name, tm, {'hps': satnet_if, 'forward_link_id': fwd_link_id, 'type': 'unicast'}, unicast_fields)

    if len(multicast_fields) > 0:
        yield TMetric(name, tm, {'hps': satnet_if, 'forward_link_id': fwd_link_id, 'type': 'multicast'}, multicast_fields)

    if len(control_fields) > 0:
        yield TMetric(name, tm, {'hps': satnet_if, 'forward_link_id': fwd_link_id, 'type': 'control'}, control_fields)

    if len(sw_upgrade_fields) > 0:
        yield TMetric(name, tm, {'hps': satnet_if, 'forward_link_id': fwd_link_id, 'type': 'sw_upgrade'}, sw_upgrade_fields)

def set_fields(type_group, type_name, set_in, add_to, subtract_from):
    if type_name in type_group:
        for metric in type_group[type_name]:
            field_key = get_field_key(metric.key)
            field_value = long(metric.value)

            set_in[field_key] = field_value

            if add_to != None:
                if field_key in add_to:
                    add_to_value = add_to[field_key]
                    add_to[field_key] = add_to_value + field_value
                else:
                    add_to[field_key] = field_value
            
            if subtract_from != None:
                if field_key in subtract_from:
                    subtract_from_value = subtract_from[field_key]
                    subtract_from[field_key] = subtract_from_value - field_value
                else:
                    subtract_from[field_key] = field_value

def get_fwd_pool_series(tm, satnet_if, fwd_link_config, fwd_pool_metrics):
    if fwd_link_config == None or fwd_link_config.fwd_link == None or fwd_link_config.fwd_link.fwd_link_id == None or fwd_link_config.fwd_link.fwd_link_id == 0:
        return
        yield

    name = 'forward.shaper.pools'
    fwd_link_id = fwd_link_config.fwd_link.fwd_link_id    
    node_names = fwd_link_config.get_fwd_pool_node_names()

    group_names = dict([(node_name, []) for node_name in node_names if 'forwardpool_' in node_name])

    [group_names[metric.meta_data].append(metric) for metric in fwd_pool_metrics if metric.meta_data in group_names ]

    for key, metrics in group_names.iteritems():
        tags = { 'forward_link_id': fwd_link_id, 'hps': satnet_if, 'forward_pool_name': key }
        fields = get_fwd_pool_fields(metrics)
        if len(fields) > 0:
            yield TMetric(name, tm, tags, fields)

def get_hub_multicast_circuit(tm, satnet_if, fwd_link_config, hub_multicast_circuit_metrics):
    if fwd_link_config == None or fwd_link_config.fwd_link == None or fwd_link_config.fwd_link.fwd_link_id == None or fwd_link_config.fwd_link.fwd_link_id == 0:
        return
        yield
    
    name = 'forward.shaper.multicast'
    fwd_link_id = fwd_link_config.fwd_link.fwd_link_id
    node_names = fwd_link_config.get_hub_multicast_circuit_node_names()

    group_names = dict([(node_name, []) for node_name in node_names if 'multicast_' in node_name])
    [group_names[metric.meta_data].append(metric) for metric in hub_multicast_circuit_metrics if metric.meta_data in group_names]

    for key, metrics in group_names.iteritems():
        hub_multicast_circuit = fwd_link_config.fwd_link.get_hub_multicast_circuit_by_node_name(key)
        if hub_multicast_circuit != None and hub_multicast_circuit.multicast_address != None:
            tags = { 'forward_link_id': fwd_link_id, 'hps': satnet_if, 'multicast_address': hub_multicast_circuit.multicast_address }
            fields = dict([(get_field_key(metric.key), long(metric.value)) for metric in metrics])
            if len(fields) > 0:
                yield TMetric(name, tm, tags, fields)

def get_fwd_pool_fields(metrics):
    result = {}

    for metric in metrics:
        field_key = get_field_key(metric.key)

        if field_key == 'eir_shaping_ratio':
            cir_overbooking = 0
            eir_shaping_ratio = 0
            if metric.value.strip() == '*' or metric.value.strip() == '-':
                cir_overbooking = 0
                eir_shaping_ratio = 1000
            if '/' in metric.value.strip():
                split = metric.value.split('/')
                if len(split) == 3:
                    if long(split[0]) < 200:
                        cir_overbooking = 1
                        eir_shaping_ratio = 0
                    else:
                        cir_overbooking = 0
                        eir_shaping_ratio = float(split[2]) * 10
            result['cir_overbooking'] = cir_overbooking
            result['eir_shaping_ratio'] = eir_shaping_ratio
        else:
            result[field_key] = long(metric.value)

    return result

def get_field_key(field):
    if field in field_map:
        return field_map[field]

    return field