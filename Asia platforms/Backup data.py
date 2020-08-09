# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/18

import datetime,os
# import tkinter
# from tkinter import ttk
import time
import stat
import pexpect
# try:
#     import win32com.client
# except ImportError:
#     print('You can install it as a root user: "pip install pypiwin32"')
#     exit(1)
try:
    import paramiko
except ImportError:
    print('You can install it as a root user: "pip install paramiko"')
    exit(1)

# win = tkinter.Tk()
# win.title("Asia platform backup")
# win.geometry("400x400+200+20")

class disPlayer(object):
    def __init__(self,alias,hostname, username, password):
        self.alias = alias
        self.hostname = hostname
        self.username = username
        self.password = password

    def connectLinuxAndOrdered(self):
        try:
            s1 = paramiko.SSHClient()
            s1.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 取消安全认证
            s1.connect(hostname=self.hostname, username=self.username, password=self.password)  # 连接linux
        except paramiko.ssh_exception.AuthenticationException as e:
            print("please check your Newtec password")
        else:
            # order="cd /home/test/"  #执行命令
            # stdin, stdout, stderr = s1.exec_command('ssh root@ami-cms-0 "ntc_automate_operational_controller_data"')
            now = datetime.datetime.utcnow().isoformat().split("T")[0].replace("-","")
            command = 'ssh root@{}-cms-0 "ntc_automate_backup_export -a /tmp/export/{}_{} -u Admin -p Admin"\n'.format(self.alias,self.alias,now)
            command1 = 'noR00t@cce$$\n'
            # conn.write(command)
            chan = s1.invoke_shell()  # 新函数
            chan.send(command + '\n')
            time.sleep(5)
            chan.send(command1 + '\n')
            time.sleep(3)
            chan.send('\n')
            time.sleep(30)
            command2 = 'scp -r root@{}-cms-0:/tmp/export/{} /tmp/\n '.format(self.alias,now)
            command3 = 'noR00t@cce$$\n'
            chan.send(command2)
            time.sleep(5)
            chan.send(command3)
            # \n是执行命令的意思，没有\n不会执行
            time.sleep(50)  # 等待执行，这种方式比较慢


            res = chan.recv(1024 * 100000)  # 非必须，接受返回消息
            chan.close()
            # result=stdout.read()  #读取执行结果
            s1.close()  # 关闭linux连接
            return res

# def disPlay(strDisplay):
#     win = tkinter.Tk()
#     win.title(com.get())
#     # win.geometry("400x400+200+20")
#     text = tkinter.Text(win, width=200, height=200)
#     text.pack(side=tkinter.RIGHT, fill=tkinter.Y)
#     text.insert(tkinter.INSERT, strDisplay)
#     # 创建滚动条
#     scroll = tkinter.Scrollbar()
#     scroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)
#     # 关联text and scroll
#     scroll.config(command=text.yview)
#     text.config(yscrollcommand=scroll.set)
#     win.mainloop()

def func():
    # dehua = win32com.client.Dispatch("SAPI.SPVOICE")
    # dehua.Speak("您好，we are geting %s hub status,Please be patient, it takes less than 150 seconds, please do not touch anything! waiting for 2 minutes please!"% com.get())
    # print("we are geting %s hub status,Please be patient, it takes less than 150 seconds"% com.get())
    # alias1 = com.get()
    strGeneral = disPlayer('tnic', "192.168.8.21", 'zwen', 'Kacific_2020')
    strGeneral.connectLinuxAndOrdered()
    str1 = strGeneral.connectLinuxAndOrdered().decode('utf-8')

    # ch = '*'
    # n = 478
    # sStr1 = n * ch + str1[478:]
    # disPlay(str1)
    # dehua.Speak("再见，bye see you")
    print(str1)

# define a variable:
# cv = tkinter.StringVar()
# com = ttk.Combobox(win,textvariable = cv)
# com.pack()
# # 设置下拉菜单
# com["value"] = ( "ami","amk","ajn","infokom-2","psn-1","psn-2","patrakom","satsol","skyreach","speedcast","stellar","telered","tnic","tnik","kacific")
# #设置默认值
# com.current(0) #0 = index
# userName = input("please input your Newtec username: ")
# passWord = input("please input your Newtec password: ")

# # bind a event:
#
# com.bind("<<ComboboxSelected>>",func) #改变值的时候执行
# win.mainloop()
from scp import SCPClient
import sys,re
import os
import subprocess

#scp file to remote node.
def scpFileToRemoteNode(user,ip,password,localsource,remotedest,port=22):

  SCP_CMD_BASE = r"""
      expect -c "
      set timeout 300 ;
      spawn scp -o StrictHostKeyChecking=no -P {port} -r {username}@{host}:{remotedest} {localsource};
      expect *password* {{{{ send {password}\r }}}} ;
      expect *\r ;
      expect \r ;
      expect eof
      "
  """.format(username=user,password=password,host=ip,localsource=localsource,remotedest=remotedest,port=port)
  SCP_CMD = SCP_CMD_BASE.format(localsource = localsource)
  print("execute SCP_CMD: ",SCP_CMD)
  p = subprocess.Popen( SCP_CMD , stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
  p.communicate()
  os.system(SCP_CMD)


def scp_remote_file(remote_file, local_file):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_client.connect(hostname='192.168.8.21', port=22, username="zwen", password="Kacific_2020")
    scp_client = SCPClient(ssh_client.get_transport(), socket_timeout=15.0)
    try:
        scp_client.get(remote_file, local_file, True)
    except Exception as e:
        print("scp remote file error: {}".format(e))

    scp_client.close()
    ssh_client.close()


if __name__ == '__main__':
    # func()
    today = datetime.datetime.utcnow().isoformat().split("T")[0].replace("-", "")

    dir = '/tmp/{}'.format(today)
    list = os.listdir(dir)
    for i in range(len(list)):
        if os.path.isfile(list[i]):
            file = os.path.join(dir, list[i])
            scp_remote_file(file, file)









