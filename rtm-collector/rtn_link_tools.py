#DIALOG VERSION: 2.2.1
satnet_command_template = 'get statistics.by_node_name.{0}.{1}\n'
satnet_command_nodes = ['root', 'multicast_traffic', 'terminal_management', 'acm_feedback']
command_fields = ['received_bytes', 'received_packets']
rcg_command_template = 'get statistics.by_node_name.rcg_{0}_{1}.{2}\n'

# input_configuration 不共享

class ReturnCapacityGroup:
    def __init__(self, input_configuration):
        self.id = None
        if 'id' in input_configuration:
            self.id = input_configuration['id']

        self.return_technology = None
        if 'return-technology' in input_configuration:
            self.return_technology = input_configuration['return-technology']

class RtnLink():
    def __init__(self, input_configuration):
        self.rtn_link_id = None
        if 'rtn-link-id' in input_configuration:
            self.rtn_link_id = input_configuration['rtn-link-id']

        self.return_capacity_groups = []

        if 'return-capacity-groups' in input_configuration and input_configuration['return-capacity-groups'] != None:
            self.return_capacity_groups = [ ReturnCapacityGroup(rcg_configuration['return-capacity-group']) for rcg_configuration in input_configuration['return-capacity-groups'] ]

class RtnLinkConfigParser:
    def __init__(self, input_configuration):
        self.rtn_link = None
        if input_configuration != None:
            self.rtn_link = RtnLink(input_configuration)

    def get_commands(self):
        result = []

        if self.rtn_link == None:
            return result

        for node in satnet_command_nodes:
            for field in command_fields:
                result.append(satnet_command_template.format(node, field))

        for rcg in self.rtn_link.return_capacity_groups:
            for field in command_fields:
                result.append(rcg_command_template.format(rcg.return_technology, rcg.id, field))

        return result

'''
rtn-link-id: 682
return-capacity-groups:
   - return-capacity-group:
      id: 744
      return-technology: s2
   - return-capacity-group:
      id: 846
      return-technology: cpm
   - return-capacity-group:
      id: 695
      return-technology: hrc_mxdma

'''