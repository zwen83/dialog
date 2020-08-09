# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/5

# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/6/3


'''

1.定义函数，下载列表页，获取内容页的地址
定义列表页的地址。
打开url地址，获取数据
解码获取到的数据
使用正则得到所有影片内容页的地址

2.主函数 main


'''
from sunckSql import SunckSql
import csv
import logging
import urllib.request
import re
from gevent import monkey
monkey.patch_all(thread=False)
import gevent
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
def get_movie_link(i):
    filmList = r"https://www.ygdy8.net/html/gndy/dyzz/list_23_{}.html".format(i)

    response = urllib.request.urlopen(filmList)
    data = response.read()
    html = data.decode("gb2312" ,"ignore")
    # <a href=\"(.*?)\" class=\"ulink\">(.*?)</a>
    urllinks = re.findall(r'<a href="(.*?)" class="ulink">(.*?)</a>',html)
    filmDict = []
    for filmurl,filname in urllinks:
        basicUrl = r"https://www.ygdy8.net/"+filmurl

        response1 = urllib.request.urlopen(basicUrl)
        data1 = response1.read().decode("gb2312","ignore")
        # print(data1)
        # downloadLink = re.search(r'bgcolor="#fdfddf"><a href="(.*?)">ftp',data1)

        pat1 = r'bgcolor="#fdfddf"><a href="(.*?)">ftp'
        DataUrl = re.compile(pat1)
        downloadLink = DataUrl.findall(data1)[0]
        print(downloadLink)
        element = {
            "name": filname,
            "Link": downloadLink
        }

        filmDict.append(element)
        # print(filmDict)
    return filmDict


def outer(func):
    def inner():
        x=1
        y=10
        func(x,y)
    return inner


def outer2(func):
    def inner():
        x=11
        y=20
        func(x,y)
    return inner

def outer3(func):
    def inner():
        x=21
        y=30
        func(x,y)
    return inner


def good(x,y):
    data = []
    s = SunckSql("192.168.14.164", "root", "root", "movie")
    for i in range (x,y):
        print("1--10")
        data += get_movie_link(i)
        if data:
            for l in data:
                name = l['name']
                print(name)
                link = l['Link']
                print(link)
                str = "insert into movielink values (null,'{}','{}',0)".format(name,link)
                print(str)
                s.insert(str)


@outer
def ten(x,y):
    good(x,y)

@outer2
def Twenty(x,y):
    good(x,y)

@outer3
def Thirty(x,y):
    good(x,y)

def main():


    FILE = ''
    g1 = gevent.spawn(ten)
    g2 = gevent.spawn(Twenty)
    g3 = gevent.spawn(Thirty)
    gevent.joinall([
        g1,g2,g3
    ])




if __name__ == '__main__':
    main()




