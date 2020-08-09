# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/17

import re
x= 1004//100
y= 1004%100
print(y)


url = '/remote-gui/KAC_SUB-1_ENCL-1/tcs-4-0/domain-17212/terminal-11183/'
a = re.split('/',url)[2].split("_")
b = a[0] + '_' +a[1]
print(b)


# print(a.getActiveBeam())  # {'RequestResult': {'Success': True}, 'RequestData': {'ActiveBeamId': 601, 'AutoBeamSelection': False, 'BeamId': 601}}
#
# print(a.getBeamData()) #{'RequestResult': {'Success': True}, 'RequestData': {'PointingCarrier1': {'Carrier': {'SymbolRate': 22000000, 'Polarization': 1, 'Freq': 11137000000, 'TimeSliceNumber': 1, 'Enabled': True, 'TSMode': 'dvbs'}}, 'MaxSkew': 0.0, 'PolarizationSkew': 0.0, 'AutomaticPointingTimeout': 0, 'OrbitalDegrees': 23.5, 'Cost': 0.0, 'InitialCarrier1': {'SymbolRate': 68000000, 'Polarization': 1, 'Freq': 10800000000, 'TimeSliceNumber': 1, 'Enabled': True, 'TSMode': 'dvbs2_acm'}, 'AcuXString': '', 'PointingCarrier2': {'Carrier': {'SymbolRate': 0, 'Polarization': 0, 'Freq': 0, 'TimeSliceNumber': 1, 'Enabled': False, 'TSMode': 'dvbs'}}, 'InitialCarrier2': {'SymbolRate': 0, 'Polarization': 0, 'Freq': 0, 'TimeSliceNumber': 1, 'Enabled': False, 'TSMode': 'dvbs2_acm'}, 'TxFrequency': 0, 'DefaultInitialCarrier': 1, 'BeamName': '', 'DefaultPointingCarrier': 1, 'GxtFileName': '', 'ExclusionZones': [], 'Hemisphere': 'east', 'TxBandwidth': 0, 'SatLatitudeVariance': 0.0, 'TxPolarization': 0}}
# # {'RequestData': {'MaxSkew': 0.0, 'DefaultInitialCarrier': 1, 'AcuXString': '', 'TxPolarization': 2, 'BeamName': '',
# #                  'PointingCarrier2': {
# #                      'Carrier': {'SymbolRate': 0, 'TSMode': 'dvbs', 'Polarization': 0, 'Freq': 0, 'Enabled': False,
# #                                  'TimeSliceNumber': 1}},
# #                  'InitialCarrier1': {'SymbolRate': 10286000, 'TSMode': 'dvbs2x', 'Polarization': 3,
# #                                      'Freq': 3710650000, 'Enabled': True, 'TimeSliceNumber': 1}, 'GxtFileName': '',
# #                  'InitialCarrier2': {'SymbolRate': 0, 'TSMode': 'dvbs2_acm', 'Polarization': 0, 'Freq': 0,
# #                                      'Enabled': False, 'TimeSliceNumber': 1}, 'PointingCarrier1': {
# #         'Carrier': {'SymbolRate': 10286000, 'TSMode': 'dvbs2x', 'Polarization': 3, 'Freq': 3710650000,
# #                     'Enabled': True, 'TimeSliceNumber': 1}}, 'AutomaticPointingTimeout': 210000,
# #                  'ExclusionZones': [], 'Cost': 0.0, 'Hemisphere': 'west', 'SatLatitudeVariance': 0.0,
# #                  'DefaultPointingCarrier': 1, 'TxBandwidth': 0, 'TxFrequency': 0, 'PolarizationSkew': 0.0,
# #                  'OrbitalDegrees': 11.0}, 'RequestResult': {'Success': True}}
#
# print(a.getTemperatures()) #{'RequestResult': {'Success': True}, 'RequestData': {'Temperatures': [{'Value': 49.0, 'Name': 'FPGA'}, {'Value': 38.0, 'Name': 'LM83'}, {'Value': 38.0, 'Name': 'MAX10'}, {'Value': 39.0, 'Name': 'MOD1'}, {'Value': 35.0, 'Name': 'MOD2'}]}}
#
# print(a.getMonitoringData())  #modem type is: Newtec MDM5010 modem. Software version: 4.3.0.5. Hardware identifier: NTC/2359.XA
#
# print(a.getActiveODUType())  #{'RequestResult': {'Success': True}, 'RequestData': {'ODUTypeId': 1}}
# print(a.getODUTypeData()) #{'RequestResult': {'Error': {'Arguments': ['Function parameters', 'ODUTypeId'], 'TextId': 'An element is missing from {0}: {1}'}, 'Success': False}}

# print(a.getSwVersion())

