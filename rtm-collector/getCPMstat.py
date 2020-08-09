# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/7/20
import threading
import requests
import json
import time
import re
import os
import subprocess
import smtplib
import time
from email.mime.text import MIMEText
import paramiko


def connectLinux():
    s1 = paramiko.SSHClient()
    s1.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 取消安全认证
    s1.connect(hostname="192.168.8.21", username="zwen", password="Speedcast_3030")  # 连接linux
    command = '''ssh root@kacific-cpmctl-kac_jav-1-1 "python test.py"\n'''
    command1 = 'noR00t@cce$$\n'
    chan = s1.invoke_shell()  # 新函数
    chan.send(command + '\n')
    time.sleep(3)
    chan.send(command1 + '\n')
    time.sleep(3)
    res = chan.recv(1024 * 100000)  # 非必须，接受返回消息
    chan.close()
    s1.close()  # 关闭linux连接
    print(res)

def cpmTS():
    try:
        auth1 = ("hno", '=kQ9+bQ(B+kh2NbD')
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        amp_stats_url = 'http://192.168.48.139:49006/remote-gui/KAC_JAV-1_ENCL-1/cpmctl-1/amp1/stats/amp'
        amp_stats_response = requests.get(amp_stats_url, auth=auth1, headers=headers, timeout=4)
        if amp_stats_response.status_code == 200:
            amp_stats_json = amp_stats_response.json()
            nbr_provisioning_terminals = amp_stats_json['prov_sits']
            # print(nbr_provisioning_terminals)
            nbr_operational_terminals = amp_stats_json['Loggedon_sits']
            print(nbr_operational_terminals)
            return nbr_operational_terminals
    except requests.exceptions.ConnectionError as e:
        raise e
        pass

def alert(nbr_operational_terminals):
    SMTPServer = "smtp.126.com"
    Sender = "victor0731@126.com"
    receiver = "zwen@idirect.net"
    passwd = "0123456789a"
    if nbr_operational_terminals <= 28:
        messageFWD = "kacific-cpmctl-kac_jav-1-1 cpm terminal drop to {}".format(nbr_operational_terminals)
        msg1 = MIMEText(messageFWD)
        msg1["Subject"] = "kacific-cpmctl-kac_jav-1-1 cpm terminal drop,please copy logs in /home/newtec/debasd.txt"
        msg1["From"] = Sender
        msg1["To"] = receiver
        mailServer = smtplib.SMTP(SMTPServer, 25)
        mailServer.login(Sender, passwd)
        mailServer.sendmail(Sender, [receiver], msg1.as_string())
        mailServer.quit()
        connectLinux()
        # print(connectLinux())

def main():
    nbr_operational_terminals= cpmTS()
    print(nbr_operational_terminals)
    alert(nbr_operational_terminals)
    timer = threading.Timer(60, main)
    timer.start()
    timer.join(1)

if __name__ == "__main__":
    cpm = threading.Thread(target=main)
    cpm.start()





