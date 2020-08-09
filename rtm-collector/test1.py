# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/5/4


#DIALOG VERSION: 2.2.1
import socket
import errno
import time
from metric import Metric
import random

class ResponseParser:
    def __init__(self, response):
        self.response = response
        self.metrics = []
        self.append = self.metrics.append

    def parse(self, line):
        idx = line.find('OK')
        if idx > -1:
            parsable_line = line[idx:]
            parts = parsable_line.split(' ')
            if len(parts) >= 4:
                split_metric = parts[1].split('.')
                key = split_metric[len(split_metric)-1]
                value = parts[3]
                metric = Metric(key, value, split_metric[len(split_metric)-2], parts[1], parts)
                self.append(metric)

    def execute(self):
        lines = self.response.split('\r\n')
        [self.parse(line) for line in lines]
        return self.metrics


class SocketMetricsCollector:
    def __init__(self):
        pass

    def execute(self, address, port, commands):
        try:
            buffer_size = 1048576 #1024K
            delimiter = '[on] >[on] >'

            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            connection.settimeout(10.0)
            connection.connect((address, port))

            try:
                command_str = ''.join([ '%s' % command for command in commands ])
                command_str += '\n'
                connection.sendall(command_str)

                data = ''
                while True:
                    read = connection.recv(buffer_size)
                    data += read
                    if read.endswith(delimiter):
                        break
            except Exception:
                return []
            finally:
                connection.shutdown(2)
                connection.close()
                connection = None

            parser = ResponseParser(data)
            return parser.execute()

        except Exception:
            return []


class MockSocketMetricsCollector:
    def __init__(self):
        pass

    def execute(self, address, port, commands):
        try:
            data = "OK: Connected\r\n"+"\r\n".join([
                command.replace("\n", " ").replace("get", "[on] >OK:")
                + "MonotonicInteger " + str(random.randint(0, 500000))
                for command in commands])
            parser = ResponseParser(data)
            return parser.execute()
        except Exception:
            return []


if __name__ == '__main__':
    collector = MockSocketMetricsCollector()
    command = ['get statistics.by_node_name.sit_{0}_{1}.received_bytes\n'.format('700','BE')]
    collector.execute('127.0.0.1',10120,command)
    print(socket.gethostname())
    terminal_qos_metrics = dict([('7000','2000')])
    print(terminal_qos_metrics)

