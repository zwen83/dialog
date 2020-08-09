# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/20
import requests
from rest import REST
import urllib.request
import json

ip = '192.168.48.136:46006'
username = 'hno'
password = 'D!@10g'
rest = REST(ip, username=username, password=password)

data = {'softwareUpdateGroup': 0, 'monitoringOption': 'Remote', 'aupcEnabled': False, 'routeAdvertisementSettings': {'satelliteNetworkId': None, 'mode': 'Static', 'locked': False, 'description': None, 'satelliteNetworkIds': [], 'modemId': {'systemId': 1492, 'domainName': 'vno', 'domainId': 355, 'name': 'Cband_T3_HRC'}, 'attributes': {}, 'satnetConnectId': None, 'id': {'systemId': 1492, 'domainName': 'vno', 'domainId': 355, 'name': '1492'}}, 'certificationRequired': False, 'lineUpSettings': {'psd': -85.0, 'nominalSfd': None, 'nominalRegulatoryPowerDbm': None, 'nominalOutputPowerDbm': -25.0, 'outputPower1DbCompression': 5.0, 'nominalBandwidthHz': 1000000, 'txPsdControlMode': 'Login Only', 'nominalIbo': None}, 'attributes': {}, 'returnClassificationProfileId': {'systemId': 4, 'domainName': 'System', 'domainId': 1, 'name': 'best-effort-only'}, 'skipCertification': 'False', 'description': '', 'bucSettings': {'bucMaxFrequencyUncertainty': 1.0, 'bucFrequencyUncertainty': 0, 'bucAndModemFrequencySynchronized': True}, 'powerSettings': {'powerControlMode': 'Nominal', 'outputPowerDbm': 1.0, 'outputPowerType': 'MODEM_POWER'}, 'switchTimeout': 60000, 'returnTechnology': 'HRC-MXDMA', 'tellinetServerAddress': '169.254.1.1', 'returnTechnologySettings': {'hrcMxDmaSettings': {'minimumSymbolRate': 30830, 'maxModCod': '32APSK9/10', 'universalLogonEnabled': False}}, 'certified': False, 'wifiSettings': None, 'beamRoamingEnabled': False, 'serviceProfileId': {'systemId': 609, 'domainName': 'vno', 'domainId': 355, 'name': 'TB_4M_2M'}, 'localPowerControlEnabled': False, 'id': {'systemId': 1492, 'domainName': 'vno', 'domainId': 355, 'name': 'Cband_T3_HRC'}, 'macAddress': '00:06:39:8c:45:8c', 'attachment': {'satelliteNetworkId': {'systemId': 293, 'domainName': 'hno', 'domainId': 7, 'name': 'SN21'}, 'returnTechnology': 'HRC-MXDMA', 'forwardPoolId': {'systemId': 698, 'domainName': 'hno', 'domainId': 7, 'name': 'FWD_pool'}, 'returnPoolId': {'systemId': 1187, 'domainName': 'hno', 'domainId': 7, 'name': 'S2-SN21'}, 'hrcModCod': 'QPSK3/10', 'forwardTechnology': 'DVB-S2 ACM', 'type': 'HRC_MXDMA_CAPACITY'}, 'communicationsOnTheMove': {'maximumAcceleration': 0.0, 'enabled': False, 'cotmFrequencyUncertainty': 0, 'maximumSpeed': 0.0}, 'type': 'MDM3310', 'positionTimeout': 60000, 'monitoringType': 'Advanced', 'encryptTraffic': None, 'debugMode': False, 'aupcRange': 6, 'forwardClassificationProfileId': {'systemId': 4, 'domainName': 'System', 'domainId': 1, 'name': 'best-effort-only'}, 'remoteGuiUrl': '/remote-gui/AMK_CBB_HM/tcs-1-0/domain-355/terminal-1492/', 'locked': False, 'networkConfigurations': [{'serviceLabel': 'VLAN2', 'ipv4': {'dhcpMode': 'Disabled', 'address': '192.168.33.1', 'lanAddressPingable': True, 'subnetRoutes': [], 'snmpEnabled': True, 'prefixLength': 24}, 'ipv6': None, 'virtualNetworkLabel': 0, 'type': 'DEDICATED', 'vlanTag': None, 'satnetsMissingNetworkConfiguration': [], 'tunnelAddress': 'fd15:a2c:8660:c828:0:6:398c:458c', 'satnetIdNetworkId': {}, 'segment4RemoteManagement': {'forwardIpv6FirewallProfileId': None, 'forwardIpv4FirewallProfileId': None, 'managed': False, 'ipv4Napt': {'lanAddress': '192.168.0.1', 'portForwardingRules': [], 'enabled': False, 'lanPrefixLength': 24}}}], 'multicastCircuitIds': [], 'satelliteNetworkConfigurations': [{'remoteGuiUrl': None, 'satelliteNetworkId': None, 'tellinetInstanceId': None, 'managementAddress': '169.254.11.3'}]}

rest.POST("modem/1492", payload=data)