"""
Fetch information and configration from the all modulator and demodulator
Export to mod_result.csv

"""
__author__ = "Ye Chuang, chye@idirect.net"
import threading
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


# Output file name


# def get_device_info():


def get_McdModel(synoptic):
    cpm = [x for x in synoptic if x["id"] ==
           "__FlowLevel_1__-CpmControlPlane"]
    if cpm:
        return "CPM"
    else:
        return "HRC"


class MyThread(threading.Thread):

    def __init__(self,hub_name,ALL_DEV,DEV):
        super().__init__()  #相当于对父类的init方法做了一个修饰。
        # 这里要调用一下父类的init方法，因为程序会优先执行子类，并覆盖父类的init方法，所以程序会报错。
        self.hub_name = hub_name
        self.ALL_DEV = ALL_DEV
        self.DEV = DEV
        self.name = self.hub_name + self.DEV
    # 重写父类的run方法
    # threading.Thread
    #     def start():
    #         self.run()

    # self.name 是继承下来的。

    def run(self):
        # Add in this list for the HUB to be checked
        # HUB = {"KAC_JAV-1": ALL_DEV_1,
        #        "KAC_JAV-2": ALL_DEV_1}
        FILE = 'mod_result2_{}_{}.csv'.format(self.hub_name,  self.DEV)
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

        for dev_slot in self.ALL_DEV:
            inf = "http://10.0.10.60/remote-gui/{}_ENCL-1/{}/cgi-bin/pogui/".format(
                self.hub_name, dev_slot)
            logger.info("http://10.0.10.60/remote-gui/{}_ENCL-1/{}/cgi-bin/pogui/{}".format(
                self.hub_name, dev_slot,self.name))

            try:
                res = requests.post(
                    url=inf + r"auth/autologin", auth=auth1, headers=headers)
                cookies = res.cookies
                # print(res.text)
                res = requests.get(
                    url=inf + r"view/deviceProps",
                    auth=auth1,
                    headers=headers).json()
                print(res)
                items = res['items']
                dev_model = next(x for x in items if x["label"] == "Device Model")[
                    'value']
                if not dev_model in MODEL:
                    logger.warning('Model not matching, skip!')
                    pass

                dev_name = next(x for x in items if x["label"] == "Device Name")[
                    'value']
                dev_role = dev_name.split('/')[-1].upper()

                synoptic = requests.get(
                    url=inf + r"view/synoptic",
                    auth=auth1,
                    headers=headers,
                    cookies=cookies).json()
                print(synoptic)
                synoptic = synoptic['items']
                dev_mng = next(x for x in synoptic if x["label"] == "Device Management")[
                    'items']
                dev_ver = next(x for x in dev_mng if x["label"] == "Software Version")[
                    'value']

                element = {
                    "Full Name": '',
                    "Hub Name": self.hub_name,
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
                        url=inf + r"view/instance/GuiConnectionsViewModulatorDetailedView/0",
                        auth=auth1,
                        headers=headers,
                        cookies=cookies).json()
                    print(res)
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
                    element['Full Name'] = self.hub_name + '.' + 'S2-MOD-' + dev_role
                if dev_model == "MCD7000":
                    element['Device Model'] = element['Device Model'] + ('_S2')
                    element['Full Name'] = self.hub_name + '.' + 'S2-DEMOD-' + dev_role
                if dev_model == "MCD7500":
                    mcd_model = get_McdModel(synoptic)
                    element['Device Model'] = element['Device Model'] + \
                                              ('_') + mcd_model
                    element['Full Name'] = self.hub_name + \
                                           '.' + mcd_model + '-DEMOD-' + dev_role
                result.append(element)

                print(element)
                element = None
                count += 1
            except Exception as e:
                print(e)
                element = {
                    "Full Name": 'NA',
                    "Hub Name": self.hub_name,
                    "Device Slot": dev_slot
                }
                result.append(element)
                # logger.warning("Skip!")

            logger.info("Count: " + str(count))
        logger.info("Done. Total: {}".format(count))
        if len(result) > 0:
            logger.info('Write to {}'.format(FILE))
            header = ['Device Role', 'Device Version', 'Device Slot', 'Device Model', 'Device Name', 'Output Level',
                      'Hub Name', 'Transmit', 'Full Name']
            print(header)
            with open(FILE, 'w', newline="") as output_file:
                dict_writer = csv.DictWriter(output_file, header)
                dict_writer.writeheader()
                print(result)
                dict_writer.writerows(result)
        else:
            logger.warnning('No result!')

if __name__ == "__main__":
    # execute only if run as a script

    BHI1 = MyThread("KAC_BHI-1",ALL_DEV_1,"1",)
    BHI1.start()

    BHI12 = MyThread("KAC_BHI-1",ALL_DEV_2,"2",)
    BHI12.start()

    SUB1 = MyThread("KAC_SUB-1",ALL_DEV_1,"1",)
    SUB1.start()

    SUB2 = MyThread("KAC_SUB-2",ALL_DEV_1,"1",)
    SUB2.start()

    JAV1 = MyThread("KAC_JAV-1",ALL_DEV_1,"1",)
    JAV1.start()

    JAV2 = MyThread("KAC_JAV-2",ALL_DEV_1,"1",)
    JAV2.start()

    BHI2 = MyThread("KAC_BHI-2",ALL_DEV_1,"1",)
    BHI2.start()



