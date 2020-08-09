# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/7/2

import csv
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fh = logging.FileHandler(__name__+'.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)
# Edit here to match the SN name. Note that for BHI, it ends with e.g. SN1, but JAV ends with SN-1
logging.getLogger('rest').setLevel(logging.DEBUG)

def ReadCsv(filename):
    fR = open(filename)
    reader = csv.DictReader(fR)
    if not reader.fieldnames or 'MacAddress' not in reader.fieldnames:
        logger.warning('file should contain a column with "MacAddress" header.')
        return
    macList = []
    for row in reader:
        macList.append(row['MacAddress'])
        logger.info('parse terminal with macaddress -- {}'.format(row['MacAddress']))
    return macList

def writeToCSV(modemList):
    FILE = 'Modem_info.csv'
    logger.info('Write modemlist - {} to {}'.format(modemList[0]['modem name'],FILE))
    header = ['time', 'modem name', 'modemType','macaddress','HPS', 'beamName','satnetName','VNO', 'hub module', 'ActiveBeamID', 'CF',
              'SymbolRate','RXvoltage','ElevationOffset','LowBand_LO','HighBand_LO','BUC_LO','temperature','cpuUsage','forwardModcod','uptime','ESN0','ReceivePower','BE_RX','BE_TX', 'CD1_RX' , 'CD1_TX','CD2_RX', 'CD2_TX', 'CD3_RX', 'CD3_TX', 'RT1_RX', 'RT1_TX', 'RT2_RX','RT2_TX','RT3_RX', 'RT3_TX']
    with open(FILE, 'a', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, header)
        dict_writer.writerows(modemList)

def writeHeader():
    FILE = 'Modem_info.csv'
    logger.info('Write CSV header to {}'.format(FILE))
    header = ['time', 'modem name','modemType','macaddress', 'HPS','beamName','satnetName', 'VNO', 'hub module', 'ActiveBeamID', 'CF',
              'SymbolRate','RXvoltage','ElevationOffset','LowBand_LO','HighBand_LO','BUC_LO','temperature','cpuUsage','forwardModcod','uptime','ESN0','ReceivePower','BE_RX','BE_TX', 'CD1_RX' , 'CD1_TX','CD2_RX', 'CD2_TX', 'CD3_RX', 'CD3_TX', 'RT1_RX', 'RT1_TX', 'RT2_RX','RT2_TX','RT3_RX', 'RT3_TX']
    with open(FILE, 'a', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, header)
        dict_writer.writeheader()


if __name__ == '__main__':
    filename = 'mac.csv'
    ReadCsv(filename)