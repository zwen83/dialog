# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/19


import time, os
import threading
import sys

threads = []

username = 'root'
passwd = 'www.awcloud.com'
ssh_ip = ['10.11.11.4',
          '10.11.11.5',
          '10.11.11.6',
          '10.11.11.7'
          ]

try:
    import pexpect
except ImportError:
    pass
else:
    import pexpect


def scp_file():
    i = 0
    for i in range(len(ssh_ip)):
        try:
            scp_command = pexpect.spawn('scp ' + scp_filename + ' root@' + ssh_ip[i] + ':/root/')
            expect_result = scp_command.expect([r'password:', r'yes/no'], timeout=30)
            if expect_result == 0:
                scp_command.sendline(passwd)

                # 这句话真的很神奇，如果不加这句话，程序会执行，但是不执行copy，请各路神人解释

            scp_command.read()
            elif expect_result == 1:
            scp_command.sendline('yes')
            scp_command.expect('assword:', timeout=30)
            scp_command.sendline(passwd)
            # don't delete this code,if your do then,the program will be faill.
        scp_command.read()
        # important
            else:
                print 'Unknow Result......'

        except pexpect.EOF:
            print 'Uploading Fail....'
            print pexpect.EOF
        except pexpect.TIMEOUR:
            print  'Uploading time out.....'
        time.sleep(2)

if '__name__' == '__main__':
    scp_file()