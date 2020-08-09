"""
Extract the basd files to destination with defined conditions

"""
__author__ = "Ye Chuang, chye@idirect.net"

import logging
import requests
import pexpect
from sched import scheduler
import time
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fh = logging.FileHandler(__name__+'.log', 'a')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)

DEBUG = True
# DEBUG = True
# HNGW IPs
ip_hmgws = ["10.75.10.180", "10.75.11.60", "10.50.10.180",
            "10.50.11.60", "10.25.10.180", "10.25.11.60"]

ip_hmgw_jav_1 = "10.50.10.180"
customer_link = 'snk-customer-links-gw'

# url_cpmctl_1 = '''http://192.168.48.139:49006/remote-gui/KAC_JAV-1_ENCL-1/cpmctl-1/amp1/stats/amp'''
# url_cpmctl_1 = '''http://cpmctl-1/amp1/stats/amp'''
# basd_cmd = '''cd /usr/local/amp/amp1/output/&&/usr/local/amp/amp1/debasd -f $(ls -t basd* | head -1) -s $(expr $(/usr/local/amp/amp1/debasd -l -f $(ls -t basd* | head -1) 2>&1 | cut -d' ' -f3) - 11000)'''
# OOOLO_cmd = '''cd /usr/local/amp/amp1/output&&cat $(ls -t ./sit* | head -1) | grep OUT | wc -l'''

s = scheduler(time.time, time.sleep)

loggedon_sits_threshold = 20
OOOLO_threshold = 500


def get_terminals(url_cpmctl):
    # From code of @zwen
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
    auth1 = ("hno", '=kQ9+bQ(B+kh2NbD')

    try:
        amp_stats_response = requests.get(
            url_cpmctl, auth=auth1, headers=headers, timeout=5)
        if amp_stats_response.status_code == 200:
            amp_stats_json = amp_stats_response.json()
            return (amp_stats_json['prov_sits'], amp_stats_json['Loggedon_sits'])
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        return None


def get_OOOLO():
    # This is a workaround
    # On .48.42 server, customer-link doesn't allow SSH forwarding so paramiko is prohibited
    # On customer-link, paramikoc cannot be used due to no root auth
    ssh_cmd = "ssh root@kacific-cpmctl-kac_jav-1-1 '/mnt/sharedfs/check_OOOLO.sh'"
    try:
        child = pexpect.spawn(ssh_cmd, timeout=10)
        child.expect(['[pP]assword: '])
        child.sendline("noR00t@cce$$")
        child.expect(pexpect.EOF)
        res = child.before.decode('utf-8').strip()
        child.close()
        return int(res)
    except Exception as e:
        logger.error(e)
        return None


def validate_terminals(threshold):
    url_cpmctl_1 = 'http://192.168.48.139:49006/remote-gui/KAC_JAV-1_ENCL-1/cpmctl-1/amp1/stats/amp'
    prov_sits, loggedon_sits = get_terminals(url_cpmctl_1)
    logger.info("prov_sits = {0}".format(prov_sits))
    logger.info("loggedon_sits = {0}".format(loggedon_sits))
    flag = loggedon_sits >= threshold
    sign = ">=" if flag else "<"
    logger.info("loggedon_sits = {0} {1} {2}".format(
        loggedon_sits, sign, threshold))
    return flag


def validate_OOOLO(threshold):
    ooolo_nb = get_OOOLO()
    flag = ooolo_nb < threshold
    sign = "<" if flag else "=>"
    logger.info("OOOLO value = {0} {1} {2}".format(ooolo_nb, sign, threshold))
    return flag


def extrac_basd():
    # This is a workaround
    # On .48.42 server, customer-link doesn't allow SSH forwarding so paramiko is prohibited
    # On customer-link, paramikoc cannot be used due to no root auth
    LINES = 10000
    filename = "/mnt/sharedfs/cpmctl_basd/basd_jav-1-1_"+datetime.utcnow().isoformat()
    ssh_cmd = '''ssh root@kacific-cpmctl-kac_jav-1-1 "/mnt/sharedfs/extract_basd.sh {0} {1}"'''.format(LINES,
                                                                                                       filename)
    logger.info("Saving basd: {0}".format(filename))
    try:
        child = pexpect.spawn(ssh_cmd, timeout=10)
        child.expect(['[pP]assword: '])
        child.sendline("noR00t@cce$$")
        child.expect(pexpect.EOF)
        child.close()
    except Exception as e:
        logger.error(e)
        return None


def action():
    try:
        logger.info("Start checking")
        logger.debug("Add valicators")
        validate_results = [validate_terminals(loggedon_sits_threshold),
                            validate_OOOLO(OOOLO_threshold)]
        if not all(validate_results):
            logger.info("Found issue. Extracting basd file")
            extrac_basd()

        logger.info("End checking")
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    delay = 60
    logger.info("Start the scheduler. Repeat every {0}s".format(delay))
    action()
    while 1:
        s.enter(delay, 1, action)
        s.run()
