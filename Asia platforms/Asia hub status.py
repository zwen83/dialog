# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/2/19


import tkinter
from tkinter import ttk
import time
try:
    import win32com.client
except ImportError:
    print('You can install it as a root user: "pip install pypiwin32"')
    exit(1)
try:
    import paramiko
except ImportError:
    print('You can install it as a root user: "pip install paramiko"')
    exit(1)

win = tkinter.Tk()
win.title("Asia Platform Status")
win.geometry("400x400+200+20")

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
            command = 'ssh root@{}-cms-0 "ntc_automate_operational_controller_data"\n'.format(self.alias)
            command1 = 'noR00t@cce$$\n'
            # conn.write(command)
            chan = s1.invoke_shell()  # 新函数
            chan.send(command + '\n')
            time.sleep(10)
            chan.send(command1 + '\n')
            # \n是执行命令的意思，没有\n不会执行
            time.sleep(30)  # 等待执行，这种方式比较慢
            res = chan.recv(1024 * 100000)  # 非必须，接受返回消息
            chan.close()
            # result=stdout.read()  #读取执行结果
            s1.close()  # 关闭linux连接
            return res

def disPlay(strDisplay):
    win = tkinter.Tk()
    win.title(com.get())
    # win.geometry("400x400+200+20")
    text = tkinter.Text(win, width=200, height=200)
    text.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    text.insert(tkinter.INSERT, strDisplay)
    # 创建滚动条
    scroll = tkinter.Scrollbar()
    scroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    # 关联text and scroll
    scroll.config(command=text.yview)
    text.config(yscrollcommand=scroll.set)
    win.mainloop()

def func(event):
    dehua = win32com.client.Dispatch("SAPI.SPVOICE")
    dehua.Speak("您好，we are geting %s hub status,Please be patient, it takes less than 150 seconds, please do not touch anything! waiting for 2 minutes please!"% com.get())
    print("we are geting %s hub status,Please be patient, it takes less than 150 seconds"% com.get())
    alias1 = com.get()
    strGeneral = disPlayer(alias1, "192.168.8.21", userName, passWord)
    strGeneral.connectLinuxAndOrdered()
    str1 = str(strGeneral.connectLinuxAndOrdered(), encoding ='utf-8')
    ch = '*'
    n = 478
    sStr1 = n * ch + str1[478:]
    disPlay(sStr1)
    dehua.Speak("再见，bye see you")

# define a variable:
cv = tkinter.StringVar()
com = ttk.Combobox(win,textvariable = cv)
com.pack()
# 设置下拉菜单
com["value"] = ( "ami","amk","ajn","infokom-2","psn-1","psn-2","patrakom","satsol","skyreach","speedcast","stellar","telered","tnic","tnik","kacific")
#设置默认值
com.current(0) #0 = index
userName = input("please input your Newtec username: ")
passWord = input("please input your Newtec password: ")

# bind a event:

com.bind("<<ComboboxSelected>>",func) #改变值的时候执行
win.mainloop()