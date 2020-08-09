#DIALOG VERSION: 2.2.1
from pysnmp.hlapi import *
import logging
from unicodedata import category

class SnmpColumnValue:
    def __init__(self, index, oid, value):
        self.index = index
        self.oid = oid
        self.value = str(value)

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

    snmp_request

    for (errorIndication, errorStatus, errorIndex, varBinds) in bulkCmd(SnmpEngine(), CommunityData(community)
                                                                        , UdpTransportTarget((ip_address, port)), ContextData(), 0, 50
                                                                        , ObjectType(ObjectIdentity(snmp_request.oid)), lexicographicMode=False):
        if errorIndication:
            logging.error('snmp get bulk operation has returned with error indication {0}'.format(errorIndication))
        elif errorStatus:
            logging.error('snmp get bulk operation has returned with error status {0}'.format(errorStatus))
        else:
            count = 0
            for varBind in varBinds:
                idx = None
                value = None

                key = '.'.join([str(x) for x in varBind[0]])
                
                for column in snmp_request.columns:
                    count = count + 1
                    if column in key:
                        idx = key.replace(column, '')
                        value = SnmpColumnValue(idx, column, varBind[1]._value)

                if idx and value:
                    idx = idx.replace('1.3.6.1.4.1', '')
                    if idx in result:
                        values = result[idx]
                        values.append(value)
                    else:
                        result[idx] = [ value ]

    return result