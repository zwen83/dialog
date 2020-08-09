#DIALOG VERSION: 2.2.1
import netsnmp
from unicodedata import category

class SnmpColumnValue:
    def __init__(self, index, oid, value):
        self.index = index
        self.oid = oid
        self.value = value

    def __repr__(self):
        return '%s: %s' % (self.oid, self.value)

class SnmpRequest:
    def __init__(self, oid, columns = []):
        self.oid = oid
        self.columns = columns

def decode_octet_string(octet_string):
    splits = octet_string.split('.')

    decoded_string = ''.join([str(unichr(int(val))) for val in splits[1:] if category(unichr(int(val)))[0]!="C"])

    return decoded_string

def get_snmp_table(ip_address, port, community, snmp_request, num_columns):
    result = {}

    session = netsnmp.Session(Version = 2, DestHost = ip_address, RemotePort = port, Community = community)
    varlist = netsnmp.VarList(netsnmp.Varbind('.{0}'.format(snmp_request.oid)))
    session_stop_index = num_columns * 25

    bulk_result = session.getbulk(0, session_stop_index, varlist)

    if bulk_result != None:
        for varbind in varlist:
            for column in snmp_request.columns:
                if column in varbind.tag:
                    start_index = varbind.tag.index(column)
                    idx = varbind.tag.replace(column, '')                    
                    idx = idx[start_index:]

                    value = SnmpColumnValue(idx, column, varbind.val)

                    if idx in result:
                        values = result[idx]
                        values.append(value)
                    else:
                        result[idx] = [ value ]

    return result