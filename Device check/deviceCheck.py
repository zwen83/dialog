"""
Fetch information and configration from the all modulator and demodulator
Export to mod_result.csv

"""
__author__ = "Ye Chuang, chye@idirect.net"

import logging
import copy
import json
import csv
from pathlib import Path
import re
import requests

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

ALL_DEV_1 = ['DEV-1-{}'.format(x) for x in range(1, 33)]
ALL_DEV_2 = ['DEV-2-{}'.format(x) for x in range(1, 33)]
ALL_HUB = {"KAC_BHI-1": ALL_DEV_1+ALL_DEV_2,
           "KAC_BHI-2": ALL_DEV_1,
           "KAC_SUB-1": ALL_DEV_1,
           "KAC_SUB-2": ALL_DEV_1,
           "KAC_JAV-1": ALL_DEV_1,
           "KAC_JAV-2": ALL_DEV_1}

# Output file name
FILE = 'mod_result2.csv'


def get_device_info():
    # Add in this list for the HUB to be checked
    # HUB = {"KAC_JAV-1": ALL_DEV_1,
    #        "KAC_JAV-2": ALL_DEV_1}
    HUB = ALL_HUB

    # Add in this list for the devics to be checked. Comment out the repeat line
    # use DEV = ALL_DEV_1 to check check dev-1-1 to DEC-1-32
    # use DEV = ALL_DEV_2 to check check dev-2-1 to DEV-2-32, mainly for BHI-1-2 which is 2nd BB rack
    # Suggest to run for HUB KAC_BHI-1, DEV-2-1 to DEV-2-32 in a seperate run
    # DEV = ["DEV-1-1", ]

    MODEL = ['MCM7500']
    # MODEL = ['MCM7500', 'MCD7500', 'MCD7000']

    auth1 = ("hno", "D!@10g")
    headers = {'Content-Type': '*/*',
               'Accept': 'application/json'}
    result = []
    count = 0
    logger.info("Start")
    hub_list = list(HUB.keys())
    for hub_name in HUB:
        DEV = HUB[hub_name]
        for dev_slot in DEV:
            inf = "http://10.0.10.60/remote-gui/{}_ENCL-1/{}/cgi-bin/pogui/".format(
                hub_name, dev_slot)
            logger.info("Connecting {} {}".format(hub_name, dev_slot))

            try:
                res = requests.post(
                    url=inf+r"auth/autologin", auth=auth1, headers=headers)
                cookies = res.cookies
                # print(res.text)
                res = requests.get(
                    url=inf+r"view/deviceProps",
                    auth=auth1,
                    headers=headers).json()
                items = res['items']
                dev_model = next(x for x in items if x["label"] == "Device Model")[
                    'value']
                if not dev_model in MODEL:
                    logger.warning('Model not matching, skip!')
                    continue
                dev_name = next(x for x in items if x["label"] == "Device Name")[
                    'value']
                dev_role = dev_name.split('/')[-1].upper()

                synoptic = requests.get(
                    url=inf+r"view/synoptic",
                    auth=auth1,
                    headers=headers,
                    cookies=cookies).json()
                synoptic = synoptic['items']
                dev_mng = next(x for x in synoptic if x["label"] == "Device Management")[
                    'items']
                dev_ver = next(x for x in dev_mng if x["label"] == "Software Version")[
                    'value']

                element = {
                    "Full Name": '',
                    "Hub Name": hub_name,
                    "Device Slot": dev_slot,
                    "Device Name": dev_name,
                    "Device Model": dev_model,
                    "Device Role": dev_role,
                    "Device Version": dev_ver,
                    "Transmit": '',
                    "Output Level": ''
                }

                if dev_model == 'MCM7500':
                    logger.info("Get MCM7500 spcific information.")

                    res = requests.get(
                        url=inf+r"view/instance/GuiConnectionsViewModulatorDetailedView/0",
                        auth=auth1,
                        headers=headers,
                        cookies=cookies).json()
                    # print(res)
                    items = res['items']
                    group = next(
                        x for x in items if x["label"] == "Configuration")
                    items = group['items']
                    group = next(
                        x for x in items if x["label"] == "Configuration Table")
                    items = group['items']
                    transmit_config = next(
                        x for x in items if x["label"] == "Transmit")
                    output_level_config = next(
                        x for x in items if x["label"] == "Output Level")
                    element["Transmit"] = transmit_config['value']
                    element["Output Level"] = output_level_config['value']
                    element['Full Name'] = hub_name+'.'+'S2-MOD-'+dev_role
                if dev_model == "MCD7000":
                    element['Device Model'] = element['Device Model']+('_S2')
                    element['Full Name'] = hub_name+'.'+'S2-DEMOD-'+dev_role
                if dev_model == "MCD7500":
                    mcd_model = get_McdModel(synoptic)
                    element['Device Model'] = element['Device Model'] + \
                        ('_')+mcd_model
                    element['Full Name'] = hub_name + \
                        '.'+mcd_model+'-DEMOD-'+dev_role
                result.append(element)

                print(element)
                element = None
                count += 1
            except Exception as e:
                print(e)
                element = {
                    "Full Name": 'NA',
                    "Hub Name": hub_name,
                    "Device Slot": dev_slot
                }
                result.append(element)
                # logger.warning("Skip!")
                continue

            logger.info("Count: "+str(count))
    logger.info("Done. Total: {}".format(count))
    return result


def get_McdModel(synoptic):
    cpm = [x for x in synoptic if x["id"] ==
           "__FlowLevel_1__-CpmControlPlane"]
    if cpm:
        return "CPM"
    else:
        return "HRC"


if __name__ == "__main__":
    # execute only if run as a script
    result = get_device_info()
    if len(result) > 0:
        logger.info('Write to {}'.format(FILE))
        header = list(result[0].keys())
        with open(FILE, 'w', newline="") as output_file:
            dict_writer = csv.DictWriter(output_file, header)
            dict_writer.writeheader()
            dict_writer.writerows(result)
    else:
        logger.warnning('No result!')
