#DIALOG VERSION: 2.2.1
fwd_link_commands = [
    'get statistics.by_node_name.root.send_rate\n',
    'get statistics.by_node_name.root.sent_volume\n',

    'get statistics.by_node_name.satnet.received_bytes\n',
    'get statistics.by_node_name.satnet.received_packets\n',
    'get statistics.by_node_name.satnet.sent_bytes\n',
    'get statistics.by_node_name.satnet.sent_packets\n',
    'get statistics.by_node_name.satnet.dropped_bytes\n',
    'get statistics.by_node_name.satnet.dropped_packets\n',
    'get statistics.by_node_name.satnet.avg_delay\n',
    'get statistics.by_node_name.satnet.send_rate\n',
    
    'get statistics.by_node_name.multicast.received_bytes\n',
    'get statistics.by_node_name.multicast.received_packets\n',
    'get statistics.by_node_name.multicast.sent_bytes\n',
    'get statistics.by_node_name.multicast.sent_packets\n',
    'get statistics.by_node_name.multicast.dropped_bytes\n',
    'get statistics.by_node_name.multicast.dropped_packets\n',
    'get statistics.by_node_name.multicast.avg_delay\n',

    'get statistics.by_node_name.control.received_bytes\n',
    'get statistics.by_node_name.control.received_packets\n',
    'get statistics.by_node_name.control.sent_bytes\n',
    'get statistics.by_node_name.control.sent_packets\n',
    'get statistics.by_node_name.control.dropped_bytes\n',
    'get statistics.by_node_name.control.dropped_packets\n',
    'get statistics.by_node_name.control.avg_delay\n',

    'get statistics.by_node_name.management.received_bytes\n',    
    'get statistics.by_node_name.management.received_packets\n',    
    'get statistics.by_node_name.management.sent_bytes\n',    
    'get statistics.by_node_name.management.sent_packets\n',    
    'get statistics.by_node_name.management.dropped_bytes\n',    
    'get statistics.by_node_name.management.dropped_packets\n',    
    'get statistics.by_node_name.management.avg_delay\n',

    'get statistics.by_node_name.control_sr.sent_volume\n',    
    'get statistics.by_node_name.management_sr.sent_volume\n',
    'get statistics.by_node_name.multicast_sr.sent_volume\n',

    'get statistics.by_terminal_name.trm_ntp.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_sw_upd.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_user_class_1_amp.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_user_class_1_cpm_s2x_hrc.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_user_class_1_ftb.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_user_class_1_hrcctl.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_user_class_1_ncr.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_user_class_1_s2xctl.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_user_class_1_stb.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_user_class_2_cse.send_symbol_rate\n',
    'get statistics.by_terminal_name.trm_user_class_2_ftb.send_symbol_rate\n'
    ]

tb_pool_template = 'forwardpool_{0}'#0 = forward-pool-id
cb_pool_template = 'forwardpool_{0}-{1}'#0 = forward-pool-id, 1 = qos-class
vno_pool_template = 'forwardpool_{0}-vno_{1}-{2}'#0 = forward-pool-id, 1 = domain-id, 2 = qos-class
hub_multicast_circuit_template = 'multicast_{0}'
command_template = 'get statistics.by_node_name.{0}.{1}\n'

fwd_pool_fields = [
    'received_bytes',
    'received_packets',
    'sent_volume',
    'sent_bytes',
    'sent_packets',
    'dropped_bytes',
    'dropped_packets',
    'avg_delay',
    'accounting_avg_shaping_ratio'
    ]

hub_multicast_circuit_fields = [
    'received_bytes',
    'received_packets',
    'sent_bytes',
    'sent_packets',
    'dropped_bytes',
    'dropped_packets',
    'avg_delay'
    ]

class HubMulticastCircuit:
    def __init__(self, input_configuration):
        self.hub_multicast_circuit_id = None

        if 'id' in input_configuration:
            self.hub_multicast_circuit_id = input_configuration['id']

        self.multicast_address = None

        if 'multicast-address' in input_configuration:
            self.multicast_address = input_configuration['multicast-address']

class FwdPool:
    def __init__(self, input_configuration):
        self.fwd_pool_id = None
        if 'id' in input_configuration:
            self.fwd_pool_id = input_configuration['id']

        self.fwd_pool_type = None
        if 'type' in input_configuration:
            self.fwd_pool_type = input_configuration['type']

        self.qos_classes = []
        self.vnos = []

        if 'qos-classes' in input_configuration and input_configuration['qos-classes'] != None:
            self.qos_classes = input_configuration['qos-classes']

        if 'vnos' in input_configuration and input_configuration['vnos'] != None:
            self.vnos = [ vno_id for vno_id in input_configuration['vnos'] ]

class FwdLink:
    def __init__(self, input_configuration):
        self.fwd_link_id = None
        if 'fwd-link-id' in input_configuration:
            self.fwd_link_id = input_configuration['fwd-link-id']

        self.fwd_pools = []

        if 'forward-pools' in input_configuration and input_configuration['forward-pools'] != None:
            self.fwd_pools = [ FwdPool(pool_configuration['forward-pool']) for pool_configuration in input_configuration['forward-pools'] ]

        self.hub_multicast_circuits = []

        if 'hub-multicast-circuits' in input_configuration and input_configuration['hub-multicast-circuits'] != None:
            self.hub_multicast_circuits = [ HubMulticastCircuit(hub_multicast_circuit_config['hub-multicast-circuit']) for hub_multicast_circuit_config in input_configuration['hub-multicast-circuits'] ]

    def get_hub_multicast_circuit_by_node_name(self, node_name):
        #get id from nodename. Nodename format = 'multicast_[system_id]'
        hub_multicast_circuit_id = int(node_name[node_name.rfind('_') + 1:])

        if self.hub_multicast_circuits != None and len(self.hub_multicast_circuits) > 0:
            hub_multicast_circuit = next((hub_multicast_circuit for hub_multicast_circuit in self.hub_multicast_circuits if hub_multicast_circuit.hub_multicast_circuit_id == hub_multicast_circuit_id), None)
            return hub_multicast_circuit

        return None

class FwdLinkConfigParser:
    def __init__(self, input_configuration):
        self.fwd_link = None
        self.commands = []

        if input_configuration != None:
            self.fwd_link = FwdLink(input_configuration)
            self.commands = self.get_commands()

    def get_fwd_pool_node_names(self):
        result = []

        if self.fwd_link == None:
            return result

        for fwd_pool in self.fwd_link.fwd_pools:
            result.append(tb_pool_template.format(fwd_pool.fwd_pool_id))
            if fwd_pool.fwd_pool_type == 'CB':
                for qos_class in fwd_pool.qos_classes:
                    if len(fwd_pool.vnos) == 0:#only add the root pool if there are no vno's specified (shaper cb pool)
                        result.append(cb_pool_template.format(fwd_pool.fwd_pool_id, qos_class))
                    for vno_id in fwd_pool.vnos:
                        result.append(vno_pool_template.format(fwd_pool.fwd_pool_id, vno_id, qos_class))

        return result

    def get_hub_multicast_circuit_node_names(self):
        result = []

        if self.fwd_link == None or self.fwd_link.hub_multicast_circuits == None:
            return result

        result = [ hub_multicast_circuit_template.format(hub_multicast_circuit.hub_multicast_circuit_id) for hub_multicast_circuit in self.fwd_link.hub_multicast_circuits ]

        return result

    def get_commands(self):
        fwd_pool_node_names = self.get_fwd_pool_node_names()
        hub_multicast_circuit_node_names = self.get_hub_multicast_circuit_node_names()

        result = fwd_link_commands

        for field in fwd_pool_fields:
            commands = [ command_template.format(node_name, field) for node_name in fwd_pool_node_names ]
            result.extend(commands)

        for field in hub_multicast_circuit_fields:
            commands = [ command_template.format(node_name, field) for node_name in hub_multicast_circuit_node_names ]
            result.extend(commands)

        return result