# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/19

import paramiko
import re
import os
import threading
from prettytable import PrettyTable
import sys
import subprocess
import time
import argparse
import pprint
from IPython.lib.pretty import pprint as prprint
import io
import datetime
import json

parser = argparse.ArgumentParser()
parser.add_argument("platform", help="specify the platform or 'all' for all known platforms, use as first argument")
parser.add_argument('-u', '--upgrade', nargs='+', help="specify devices to upgrade")
parser.add_argument('-l', '--list', action="store_true", default=False,
                    help="this option will list all devices found for the specified platform")
# parser.add_argument('-l','--list', help="list all devices found")
parser.add_argument('-r', '--reboot', nargs='+', help="reboot specified devices")
parser.add_argument('-f', '--versionsfile', help="specify a file with urls for each devicetype", type=open)
parser.add_argument('-p', '--past history', help="report what whas updated when")
args = parser.parse_args()
print(args)


def nice_date(stringdate):
    """ TimeStamp=20180301150608 into dd/mm/yyyy hh:mm:ss"""
    m = re.match(r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', stringdate)
    return m.group(3) + "/" + m.group(2) + "/" + m.group(1) + " " + m.group(4) + ":" + m.group(5) + ":" + m.group(6)


class Firmware:
    def __init__(self, dev, raw_buildinfo):
        """
        struct to describe a software-build taken from build.xml
        <BuildInfo Product="M6100" Buildtype="RMT" TimeStamp="20170404083842" Release="M6100_1.6D.1.79768" Node="324415" />
        <BuildInfo Product="MCD7000" Buildtype="RMT" TimeStamp="20170711125826" SW_ID="MCD7000-HRC" SW_VERSION="2.0.2.6" Release="2.0.2.6" Node="357017" />
        """
        self.dev = dev
        r = re.compile(r'BuildInfo Product="(.*)" Buildtype="(.*)" TimeStamp="(.*)" Release="(.*)" Node="(.*)"')
        m = r.search(raw_buildinfo)
        if m:
            self.Product = m.group(1)
            self.Buildtype = m.group(2)
            self.TimeStamp = nice_date(m.group(3))
            self.SW_ID = "N/A"
            self.SW_VERSION = "N/A"
            self.Release = m.group(4)[0:30]
            self.Node = m.group(5)
            self.matched_buildinfo_version = "v1"
        r = re.compile(
            r'BuildInfo Product="(.*)" Buildtype="(.*)" TimeStamp="(.*)" SW_ID="(.*)" SW_VERSION="(.*)" Release="(.*)" Node="(.*)"')
        m = r.search(raw_buildinfo)
        if m:
            self.Product = m.group(1)
            self.Buildtype = m.group(2)
            self.TimeStamp = nice_date(m.group(3))
            self.SW_ID = m.group(4)
            self.SW_VERSION = m.group(5)
            self.Release = m.group(6)[0:30]
            self.Node = m.group(7)
            self.matched_buildinfo_version = "v2"
        r = re.compile(r'BuildInfo OLDBDM')
        m = r.search(raw_buildinfo)
        if m:
            self.Product = "OLDBDM"
            self.BuildType = "N/A"
            self.TimeStamp = "N/A"
            self.SW_ID = "N/A"
            self.SW_VERSION = "N/A"
            self.Release = "N/A"
            self.Node = "N/A"
            self.matched_buildinfo_version = "v3"

        if not hasattr(self, "matched_buildinfo_version"):
            raise Exception("Buildinfo error")
        self.determine_upgrade_role()
        print("at end of constructor: " + repr(self))

    def __repr__(self):
        return "#Firmware [#BB %s/%s SN=%s] P=%s T=%s SW_ID=%s V=%s R=%s" % (
        self.dev.platform.name, self.dev.devname, self.dev.serialno, self.Product, self.TimeStamp, self.SW_ID,
        self.SW_VERSION, self.Release)

    def json_dict(self):
        return dict(Product=self.Product, BuildTime=self.TimeStamp, SW_ID=self.SW_ID, SW_VERSION=self.SW_VERSION,
                    Release=self.Release)

    def determine_upgrade_role(self):
        """
        this function should determine the role of the firmware found. This is the key into the new_firmware dict.
        possible values: M6100, MCM7500, MCD6000-S2, MCD6000-HRC, MCD7000-S2, MCD7000-HRC, MCD7000-CPM
        """
        tmp = "{}-{}-{}".format(self.Product, self.SW_ID, self.Release).upper()
        if self.Product == "M6100":
            self.dev.upgrade_role = "M6100"
        elif self.Product == "MCM7500":
            self.dev.upgrade_role = "MCM7500"
        elif self.Product == "MCD7000" and re.search(r'HRC', tmp):
            self.dev.upgrade_role = "MCD7000-HRC"
        elif self.Product == "MCD7000" and re.search(r'CPM', tmp):
            self.dev.upgrade_role = "MCD7000-CPM"
        elif self.Product == "MCD7000":
            self.dev.upgrade_role = "MCD7000-S2"
        elif self.Product == "MCD6000" and re.search(r'HRC', tmp):
            self.dev.upgrade_role = "MCD6000-HRC"
        elif self.Product == "MCD6000":
            self.dev.upgrade_role = "MCD6000-S2"
        else:
            print("couldn't determine a upgrade-role")
            self.dev.upgrade_role = "N/A"
            # raise Exception("unsupported upgrade_role")


"""
ping -c2 dev-1
'PING DEV-1 (172.20.0.101) 56(84) bytes of data.\n'
'64 bytes from DEV-1 (172.20.0.101): icmp_seq=1 ttl=64 time=1.08 ms\n'
'64 bytes from DEV-1 (172.20.0.101): icmp_seq=2 ttl=64 time=5.44 ms\n'
'\n'
'--- DEV-1 ping statistics ---\n'
'2 packets transmitted, 2 received, 0% packet loss, time 1006ms\n'
'rtt min/avg/max/mdev = 1.080/3.260/5.440/2.180 ms\n'
ping -c2 dev-2
'PING DEV-2 (172.20.0.102) 56(84) bytes of data.\n'
'From CMS-2 (172.20.11.3) icmp_seq=1 Destination Host Unreachable\n'
'From CMS-2 (172.20.11.3) icmp_seq=2 Destination Host Unreachable\n'
'\n'
'--- DEV-2 ping statistics ---\n'
'2 packets transmitted, 0 received, +2 errors, 100% packet loss, time 3007ms\n'
'pipe 2\n'
"""


class BaseBandDevice:
    def __init__(self, platform, dev_name):
        self.devname = dev_name
        self.platform = platform
        self.enable_rootaccess()
        if self.upgrade_role != "OLDBDM_CPM":
            self.serialno = self.serialno()
            self.diarole = self.diarole()
            self.probe_device()
        else:
            self.serialno = "OLDBDM-N/A"
            self.firmware = Firmware(self, "BuildInfo OLDBDM")
            self.diarole = "OLDBDM-N/A"

    def __repr__(self):
        return "#BB Name=%s SN=%s" % (self.devname, self.serialno)

    def json_dict(self):
        return dict(sn=self.serialno, firmware=self.firmware.json_dict())

    def enable_rootaccess(self):
        dev = self.devname
        print("enabling rootaccess for " + dev)
        gw_ssh_transport = self.platform.gw_ssh_transport
        dest_addr = (dev, 22)
        local_addr = ('127.0.0.1', 1234)
        try:
            with self.platform.ssh_connections_semaphore:
                channel = gw_ssh_transport.open_channel("direct-tcpip", dest_addr, local_addr)
                remote_client = paramiko.SSHClient()
                remote_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print("connect to portforward")
                remote_client.connect('127.0.0.1', 1234, 'newtec', 'sixtusabdij', sock=channel, allow_agent=False,
                                      look_for_keys=False)
                stdin, stdout, stderr = remote_client.exec_command("debug rootaccess enable'\n")
                stdin.close()
                print(stdout.read())
            print("root access enabled on " + dev)
            self.upgrade_role = ""
        except paramiko.ssh_exception.SSHException as e:
            print("couldn't request channel for port-forward, probably a BDM")
            self.upgrade_role = "OLDBDM_CPM"
            print(e)
        except OSError as e:
            print("os error while connecting to " + self.platform.name)
            print(e)

    def probe_device(self):
        buildinfo = self.exec_cmd("cat /build.xml")
        m = re.search(r"(<BuildInfo.* />)", str(buildinfo))
        if m:
            self.firmware = Firmware(self, m.group(1))

    def exec_newtec_cli_cmd(self, cmd):
        gw_ip = self.platform.gw_ip
        dev = self.devname
        fullcmd = "sshpass -p westvleteren ssh " + self.platform.ssh_args + " -o ProxyCommand='sshpass -p " + \
                  self.platform.data["gw_ssh_pass"] + " ssh " + self.platform.ssh_args + " " + self.platform.data[
                      "gw_ssh_username"] + "@" + gw_ip + " nc " + dev + " 22' root@" + dev + " clish -u newtec -c '" + cmd + "'"
        print("Dev " + dev + " ==> ntccmd: " + repr(fullcmd))
        try:
            with self.platform.ssh_connections_semaphore:
                output = subprocess.run(fullcmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(self.devname + " " + repr(output))
            return output.stdout.decode()
        except subprocess.CalledProcessError as e:
            print("e: " + repr(e))
            print("e stdout: " + e.stdout.decode())
            print("e stderr: " + e.stderr.decode())
            return e.stdout.decode()

    ntccmd = exec_newtec_cli_cmd

    def exec_cmd(self, cmd):
        gw_ip = self.platform.gw_ip
        dev = self.devname
        prefix = "sshpass -p westvleteren ssh " + self.platform.ssh_args + " -o ProxyCommand='sshpass -p " + \
                 self.platform.data["gw_ssh_pass"] + " ssh " + self.platform.ssh_args + " " + self.platform.data[
                     "gw_ssh_username"] + "@" + gw_ip + " nc " + dev + " 22' root@" + dev + " "
        print("Dev " + dev + " ==> exec_cmd: " + repr(prefix + cmd))
        try:
            with self.platform.ssh_connections_semaphore:
                output = subprocess.run(prefix + cmd, shell=True, check=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            print(self.devname + " " + repr(output))
            return "START " + self.devname + " START\n" + output.stdout.decode() + "END " + self.devname + " END"
        except subprocess.CalledProcessError as e:
            print("e: " + repr(e))
            print("e stdout: " + e.stdout.decode())
            print("e stderr: " + e.stderr.decode())
            raise

    def check_if_up(self):
        try:
            result = self.platform.exec_cmd("ping -c4 " + self.devname)
        except subprocess.CalledProcessError as e:
            print("ERROR: couldn't ping to " + devname)
            print("e: " + repr(e))
            print("e stdout: " + e.stdout.decode())
            print("e stderr: " + e.stderr.decode())
        else:
            return True

    def wait_for_dev(self):
        dev = self.devname
        gw_ip = self.platform.gw_ip
        up = False
        sleeptime = 5
        while True:
            try:
                print(self.platform.exec_cmd("ping -c4 " + dev))
            except subprocess.CalledProcessError as e:
                print(dev + " not yet up, no ping yet")
                print("e: " + repr(e))
                print("e stdout: " + e.stdout.decode())
                print("e stderr: " + e.stderr.decode())
                time.sleep(sleeptime)
            except RuntimeError as e:
                print(e)
                print(dev + ": runtime error")
                time.sleep(sleeptime)
            else:
                break
            print("sleeping 5 secs")
            time.sleep(sleeptime)
        up = True
        self.enable_rootaccess()
        print(dev + " up now")

    def reboot_without_wait(self):
        print(self.devname + ": doing a reboot without wait")
        print(self.exec_cmd("reboot"))
        time.sleep(3)

    def reboot(self):
        print(self.devname + ": doing a reboot")
        print(self.exec_cmd("reboot"))
        time.sleep(5)
        self.wait_for_dev()

    def fetch_image(self, url):
        installer_name = url.rpartition('/')[2]
        print(installer_name)
        if os.path.isfile("/tmp/" + installer_name):
            return "already fetched"
        try:
            output = subprocess.run("wget " + url + " -O /tmp/" + installer_name, shell=True, check=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(repr(output))
        except subprocess.CalledProcessError as e:
            print("e: " + repr(e))
            print("e stdout: " + e.stdout.decode())
            print("e stderr: " + e.stderr.decode())
            raise

    def upload_file(self, url):
        gw_ip = self.platform.gw_ip
        dev = self.devname
        print(self.exec_cmd("ls -lrt /tmp"))
        print(self.exec_cmd("df -m"))
        print(repr(url))
        installer_name = url.rpartition('/')[2]
        print(installer_name)
        try:
            self.fetch_image(url)
            cmd = "sshpass -p westvleteren scp " + self.platform.ssh_args + " -o ProxyCommand='sshpass -p " + \
                  self.platform.data["gw_ssh_pass"] + " ssh " + self.platform.ssh_args + " " + self.platform.data[
                      "gw_ssh_username"] + "@" + gw_ip + " nc " + dev + " 22' /tmp/" + installer_name + " root@" + dev + ":/tmp/installer.bin"
            with self.platform.ssh_connections_semaphore:
                output = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(self.devname + ": " + repr(output))
            # output = subprocess.run("rm -f /tmp/"+installer_name, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # print(repr(output))
        except subprocess.CalledProcessError as e:
            print("e: " + repr(e))
            print("e stdout: " + e.stdout.decode())
            print("e stderr: " + e.stderr.decode())
            raise

    def upgrade(self, url):
        self.upload_file(url)
        print(self.exec_cmd(
            "'openssl aes-256-cbc -pass pass:pkNFEj2DUuFtz5pG -d -in /tmp/installer.bin -out /mnt/config/ueinstaller.bin'"))
        print(self.exec_cmd("rm -rf /tmp/installer.bin"))
        print(self.exec_cmd("cat /proc/cmdline"))
        print(self.devname + ": doing => sh /mnt/config/ueinstaller.bin")
        print(self.exec_cmd("sh /mnt/config/ueinstaller.bin"))
        self.reboot()
        self.probe_device()
        print(self.devname + " software after installation: " + repr(self.firmware))


class BB(BaseBandDevice):
    def __init__(self, platform, dev_name):
        BaseBandDevice.__init__(self, platform, dev_name)
        print("at end of constructor: " + repr(self))

    def serialno(self):
        return self.ntccmd("device identification serialnumber get").strip()

    def diarole(self):
        return self.ntccmd("device identification label get").strip()


class Platform:
    platforms = {"dia1": "192.168.86.11", "dia2": "192.168.86.23", "dia3": "192.168.86.31", "dia4": "192.168.86.43",
                 "dia5": "192.168.86.50", "dia6": "192.168.86.60", "dia7": "192.168.86.73", "dia9": "192.168.86.93",
                 "dia10": "192.168.80.163", "diaci": "192.168.86.187", "corosat": "192.168.90.13",
                 "diaxif1": "192.168.82.41", "diaplato3": "192.168.84.43"}
    platforms_by_ip = {v: k for k, v in platforms.items()}
    defaults_generic = {"gw_ssh_port": 22, "gw_ssh_username": "newtec", "gw_ssh_pass": "s3p"}
    defaults_per_platformtype = {"XIF": {"gw_ssh_username": "root", "gw_ssh_pass": "root"}}
    per_platform_data = {"dia2": {}}
    ssh_args = "-q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o GSSAPIAuthentication=no"

    def __init__(self, platform, dev_list=None):
        self.devices = {}
        self.ssh_connections_semaphore = threading.Semaphore(10)
        self.gw_ip, self.name = self.resolve_platform(platform)
        self.platform_type = self.platform_type(self.name)
        self.merge_platform_dicts(self.platform_type, self.name)
        self.connect_to_gw(self.gw_ip)
        self.dev_list = dev_list
        if dev_list is None:
            self.detect_bb_devices()
            self.dev_list = self.devices_detected
            self.devices = self.probe_bb_devices()
        else:
            for dev_name in dev_list:
                dev_h = BB(self, dev_name)
                self.devices[dev_name] = dev_h
        print("at end of constructor: " + repr(self))

    def __repr__(self):
        return "#Platform name=%s/ip=%s/type=%s" % (self.name, self.gw_ip, self.platform_type)

    def json_dict(self):
        json_dict_for_devs = {}
        for k, v in self.devices.items():
            json_dict_for_devs[k] = v.json_dict()
        return dict(name=self.name, ip=self.gw_ip, platformtype=self.platform_type, devs=json_dict_for_devs)

    def write_json(self):
        d = datetime.datetime.now()
        s = d.strftime("%d%m%y_%H%M")
        with open("history/platform_" + self.name + "_" + s + ".json", "w") as j:
            j.write(json.dumps(self.json_dict(), indent=4, sort_keys=True))

    def array_of_devhashes(self):
        d = datetime.datetime.now()
        s = d.strftime("%d%m%y_%H%M")
        array_of_devhashes = []
        for k, v in self.devices.items():
            devhash = {"platform_name": self.name, "device_name": v.devname, "sno": v.serialno,
                       "fwProduct": v.firmware.Product, "fwTimeStamp": v.firmware.TimeStamp, "SW_ID": v.firmware.SW_ID,
                       "SW_VERSION": v.firmware.SW_VERSION, "Release": v.firmware.Release}
            array_of_devhashes.append(devhash)
        print(repr(array_of_devhashes))
        return array_of_devhashes

    def platform_type(self, platform_name):
        platforms_per_type = {"1IF": ["dia1", "dia2", "dia3", "dia5", "dia6"], "4IF": ["dia4", "dia7", "dia9", "dia10"],
                              "XIF": ["diaxif1", "diaplato3"]}
        platform_list = [k for (k, v) in platforms_per_type.items() if platform_name in v]
        print(platform_list)
        return platform_list[0]

    def upgrade_devices(self, dev_list, new_firmware):
        threads = []
        for dev in dev_list:
            dev_h = self.devices[dev]
            upgrade_role = dev_h.upgrade_role
            fw_url = new_firmware[upgrade_role]
            print(fw_url)
            t = threading.Thread(target=upgrade, name="thread_upgrade_dev-" + str(dev), args=(dev_h, fw_url))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

    def wait_for_devs(self, dev_list):
        for dev in dev_list:
            dev_h = self.devices[dev]
            dev_h.wait_for_dev()

    def resolve_platform(self, platform):
        m = re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", platform)
        if m:
            self.gw_ip = platform
            self.name = self.platforms_by_ip[platform.strip()]
        elif platform in self.platforms.keys():
            self.gw_ip = self.platforms[platform]
            self.name = platform
        else:
            raise Exception("cannot findout which platform to connect")
        print("gw_ip: " + self.gw_ip)
        print("platform_name: " + self.name)
        return [self.gw_ip, self.name]

    def probe_bb_devices(self):
        threads = []
        self.devices = {}
        print("probing dev_list: " + repr(self.dev_list))
        dev_names = self.dev_list
        platform = self
        for dev_name in dev_names:
            t = threading.Thread(target=probing, name="thread_probing_" + str(dev_name), args=(platform, dev_name))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        print("test" + repr(self.devices))
        return self.devices

    def format_baseband_devices(self):
        print("platform: " + self.name)
        t = PrettyTable(['Dev', 'SN', 'Product', 'Buildtime', 'SW_ID', 'Release', 'Upgrade role', 'Dialog role'])
        dev_list = self.devices.keys()
        pairs = []
        for dev in dev_list:
            m = re.search(r'.*-(\d+)\Z', dev)
            if m:
                pairs.append([int(m.group(1)), dev])
            else:
                raise "device format error"
        pairs.sort(key=lambda x: x[0])
        print(repr(pairs))
        for no, dev in pairs:
            v = self.devices[dev]
            t.add_row(
                [dev, v.serialno, v.firmware.Product, v.firmware.TimeStamp, v.firmware.SW_ID, v.firmware.Release[:40],
                 v.upgrade_role, v.diarole])
        return t

    def merge_platform_dicts(self, platform_type, platform_name):
        if platform_name in self.per_platform_data.keys():
            values_per_platform = self.per_platform_data[platform_name]
        else:
            values_per_platform = {}
        if platform_type in self.defaults_per_platformtype.keys():
            values_from_platform_type = self.defaults_per_platformtype[platform_type]
        else:
            values_from_platform_type = {}
        self.data = self.defaults_generic.copy()
        self.data.update(values_from_platform_type)
        self.data.update(values_per_platform)
        print(self.data)

    def connect_to_gw(self, gw_ip):
        print("connecting to platform " + self.name)
        try:
            self.gw_ssh_client = paramiko.SSHClient()
            self.gw_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.gw_ssh_client.connect(gw_ip, self.data["gw_ssh_port"], self.data["gw_ssh_username"],
                                       self.data["gw_ssh_pass"], allow_agent=False, look_for_keys=False)
            self.gw_ssh_transport = self.gw_ssh_client.get_transport()
        except paramiko.ssh_exception.SSHException as e:
            print("ssh exception")
            print(e)
        except OSError as e:
            print("os error while connecting to " + platform)
            print(e)

    def detect_bb_devices(self):
        self.devices_detected_lock = threading.Lock()
        self.devices_detected = []
        threads = []
        if self.platform_type == "XIF":
            for bbrack in range(1, 3):
                for devno in range(1, 33):
                    t = threading.Thread(target=handle_ping, name="thread_dev-" + str(bbrack) + "-" + str(devno),
                                         args=("dev-" + str(bbrack) + "-" + str(devno), self))
                    threads.append(t)
                    t.start()
        else:
            for devno in range(1, 19):
                t = threading.Thread(target=handle_ping, name="thread_dev-" + str(devno),
                                     args=("dev-" + str(devno), self))
                threads.append(t)
                t.start()
        for t in threads:
            t.join()

    def exec_cmd(self, cmd):
        prefix = "sshpass -p " + self.data["gw_ssh_pass"] + " ssh " + self.ssh_args + " " + self.data[
            "gw_ssh_username"] + "@" + self.gw_ip + " "
        print("Gw " + self.name + " ==> exec_cmd: " + repr(prefix + cmd))
        with self.ssh_connections_semaphore:
            output = subprocess.run(prefix + cmd, shell=True, check=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        print(repr(output))
        return output.stdout.decode()


def handle_ping(devname, platform):
    cmd = "ping -c2 " + devname
    try:
        result = platform.exec_cmd(cmd)
    except subprocess.CalledProcessError as e:
        print("ERROR: couldn't ping to " + devname)
        print("e: " + repr(e))
        print("e stdout: " + e.stdout.decode())
        print("e stderr: " + e.stderr.decode())
    else:
        for line in io.StringIO(result):
            if re.match(r'2 packets transmitted, 2 received, 0% packet loss', line):
                with platform.devices_detected_lock:
                    platform.devices_detected.append(devname)


def upgrade(dev_h, fw_url):
    dev_h.upgrade(fw_url)


def probing(platform, dev_name):
    platform.devices[dev_name] = BB(platform, dev_name)


def probe_all_platforms():
    devices_array = []
    platforms_datastructure = {}
    d = datetime.datetime.now()
    s = d.strftime("%d%m%y_%H%M")
    # platforms_to_check = ["dia1", "dia2", "dia3", "dia4", "dia5", "dia6", "dia7", "dia9", "dia10", "diaxif1", "diaplato3"]
    platforms_to_check = ["dia1", "dia2", "dia3", "dia4", "dia5", "dia6", "dia7", "diaxif1", "diaplato3"]
    platform_string = "_".join(platforms_to_check)
    with open("history/platform-device-version_" + s + "_" + platform_string + ".txt", "w") as file:
        for platform in sorted(platforms_to_check):
            p = Platform(platform)
            platforms_datastructure[platform] = p
            table = p.format_baseband_devices()
            file.write("platform: " + p.name + "\n")
            file.write(str(table))
            file.write("\n")
            # with open("history/platform_"+platform+"_"+s+".json","w") as j:
            #    j.write(json.dumps(p.json_dict(), indent=4, sort_keys=True))
            devices_array += p.array_of_devhashes()
    counter = 1
    for devices in devices_array:
        devices["id"] = counter
        counter += 1

    with open("history/" + platform_string + "_" + s + ".json", "w") as file:
        file.write(json.dumps(devices_array, indent=4, sort_keys=True))

    os.remove("/var/www/html/latestdate.html")
    os.remove("/var/www/html/platformdata.json")
    with open("/var/www/html/latestdate.html", "w") as file:
        file.write(s + "\n")
    os.symlink("/home/newtec/sgu/history/" + platform_string + "_" + s + ".json", "/var/www/html/platformdata.json")


dev_types = ["M6100", "MCM7500", "MCD6000", "MCD7000"]
base_firmware = {}
base_firmware["M6100"] = "http://192.168.1.15/index.php?download=/259454/installer_M6100_1.6D.0.73523.bin"
base_firmware["MCM7500"] = ""
base_firmware["MCD6000-S2"] = "http://192.168.1.15/index.php?download=/192667/installer_MCD6000_2.1.8.60374.bin"
base_firmware["MCD6000-HRC"] = "http://192.168.1.15/index.php?download=/356555/installer_MCD6000-HRC_1.3.0.2.bin"
base_firmware["MCD7000-S2"] = "http://192.168.1.15/index.php?download=/237992/installer_MCD7000_3.1.2.70239.bin"
base_firmware["MCD7000-HRC"] = "http://192.168.1.15/index.php?download=/356563/installer_MCD7000-HRC_2.0.2.5.bin"
base_firmware["MCD7000-CPM"] = "http://192.168.1.15/index.php?download=/357934/installer_MCD7000-4CPM_1.0.1.24.bin"

new_firmware = {}
new_firmware["M6100"] = "http://ntcl2b.newtec.eu/index.php?download=/377534/installer_M6100_1.6D.1.83485.bin"
new_firmware["MCM7500"] = ""
new_firmware["MCD6000-S2"] = "http://192.168.1.15/index.php?download=/193535/installer_MCD6000_2.1.9.60681.bin"
new_firmware["MCD6000-HRC"] = "http://192.168.1.15/index.php?download=/367807/installer_MCD6000-HRC_1.3.0.3.bin"
new_firmware["MCD7000-S2"] = "http://192.168.1.15/index.php?download=/297429/installer_MCD7000_3.2.1.76664.bin"
new_firmware["MCD7000-HRC"] = "http://192.168.1.15/index.php?download=/357017/installer_MCD7000-HRC_2.0.2.6.bin"
new_firmware["MCD7000-CPM"] = "http://192.168.1.15/index.php?download=/359896/installer_MCD7000-4CPM_1.0.1.25.bin"


def process_firmware_file(filehandle):
    new_firmware = {}
    r = re.compile(r'(.*?)="(.*)"')
    for line in filehandle:
        m = r.match(line)
        if m:
            if not m.group(1).startswith("#"):
                new_firmware[m.group(1)] = m.group(2)
    filehandle.close()
    pprint.pprint(new_firmware)
    return new_firmware


def validate_device_list(dev_list):
    for dev in dev_list:
        if not re.match(r'dev-\d+(-\d+)?', dev):
            raise Exception("device name error")
    print("device validation succeeded:" + repr(dev_list))


if args.versionsfile:
    new_firmware = process_firmware_file(args.versionsfile)
    print(repr(new_firmware))

if args.upgrade:
    start = datetime.datetime.now()
    platform = Platform(args.platform, args.upgrade)
    validate_device_list(args.upgrade)
    print(platform.format_baseband_devices())
    platform.write_json()
    platform.upgrade_devices(args.upgrade[:], new_firmware)
    platform.probe_bb_devices()
    print(platform.format_baseband_devices())
    platform.write_json()
    end = datetime.datetime.now()
    delta = end - start
    print("upgrade took: " + str(delta.seconds) + " secs")
elif args.reboot:
    platform = Platform(args.platform, args.reboot)
    for dev in args.reboot:
        dev_h = platform.devices[dev]
        print("rebooting specified devices")
        dev_h.reboot_without_wait()
        print(dev + " rebooted")
    platform.wait_for_devs(args.reboot)
elif args.list:
    if args.platform == "all":
        probe_all_platforms()
    else:
        platform = Platform(args.platform)
        print(platform.format_baseband_devices())
        platform.write_json()
else:
    raise Exception("option combination not supported")

"""
python3 upgrade.py dia2 -l
python3 upgrade.py dia2 -r dev-1
python3 upgrade.py dia2 -u dev-1 dev-2
python3 upgrade.py dia2 -u dev-1 dev-2 -f upgradefile.txt
python3 upgrade.py all -l
"""