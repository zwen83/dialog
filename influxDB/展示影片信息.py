# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/5
import socket
import threading,requests
from influxdb import InfluxDBClient


def getTSDB():

    iplist = ["192.168.48.139:49114",
           "192.168.48.139:49212",
           "192.168.48.139:49312",
           "192.168.48.139:49513",
           "192.168.48.139:49612",
           "192.168.48.139:49712",
           "192.168.48.139:50214",
           "192.168.48.139:50312",
           "192.168.48.139:49914",
           "192.168.48.139:50012",
           "192.168.48.139:50513",
           "192.168.48.139:50612",
           "192.168.48.139:50813",
           "192.168.48.139:50912"]
    listdata = []
    for ip in iplist:
        try:
            ip = 'http://{}'.format(ip)
            query1 = '''select * from "forward.shaper" where "type"='unicast' and time > now()-10m limit 1'''
            collectmethod = '/query?db=telegraf&q=' + query1
            url = ip + collectmethod
            auth1 = ('hno', '=kQ9+bQ(B+kh2NbD')
            headers1 = {'Content-Type': '*/*',
                        'Accept': 'text/html'}
            res = requests.post(url=url, auth=auth1, headers=headers1)
            cookies = res.cookies
            result = requests.get(url, headers=headers1, cookies=cookies)
            resData = result.json()
            print(resData)
            listdata.append(resData)
            print(listdata)
        except:
            pass
    return listdata

# web服务器返回固定内容

def run(ck, ip,res):
    print(res)
    username = ck.recv(1024)
    if not username:
        print(" %s custom logoff"% str(ip))
        ck.close()
    response_line = "HTTP/1.1 200 OK\r\n"
    response_header = "Server:Python20WS/2.1\r\n"
    response_header += "Content-type:text/html;charset=utf-8\r\n"
    response_blank = "\r\n"
    response_body = "[<a href='%s'>%s</a>] <br>" % (res[0]['results'][0]['series'][0]['columns'],res[0]['results'][0]['series'][0]['columns'])
    response_data = response_line + response_header + response_blank + response_body
    for row in res:
        print(row)
        response_body += "[<a href='%s'>%s</a>] <br>" % (row['results'][0]['series'][0]['values'],row['results'][0]['series'][0]['values'])

    response_data = response_line + response_header + response_blank + response_body
    ck.send(response_data.encode())
    ck.close()


def start(res):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    server.bind(("192.168.3.16", 8080))
    server.listen(128)

    while True:
        ck, ip = server.accept()
        print("new customer:",ip)
        t = threading.Thread(target=run, args=(ck, ip,res,))
        t.start()
        t.join()
        ck.close()
    # server.close()


if __name__ == '__main__':
    res=getTSDB()
    start(res)
