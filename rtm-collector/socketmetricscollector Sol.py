#DIALOG VERSION: 2.2.1
import socket
import errno
import time
# from metric import Metric
import random

class Metric:
    def __init__(self, key, value, meta_data = '', full_metric = '', parts = []):
        self.key = key
        self.value = value
        self.meta_data = meta_data
        self.full_metric = full_metric
        self.parts = parts

    def format(self):
        output = '%s,%s value=' % (self.key, ','.join(['%s=%s' % (key, value) for (key, value) in self.tags.items()]))

        if 'str' in str(type(self.value)) or 'unicode' in str(type(self.value)):
            output = '%s%s\n' % (output, str(self.value))
        else:
            output = '%s"%f"\n' % (output, self.value)

        return output


class ReponseParser:
    def __init__(self, response):
        self.reponse = response
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
                metric = Metric(key, value, split_metric[len(split_metric)-2], parts[1])
                self.append(metric)

    def execute(self):
        lines = self.reponse.split('\r\n')
        [self.parse(line) for line in lines]
        return self.metrics


class SocketMetricsCollector:
    def execute(self, address, port, command_str):
        # try:
        print(address, port)
        buffer_size = 1048576 #1024K
        delimiter = '[on] >[on] >'

        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        connection.settimeout(10.0)
        connection.connect((address, port))

        try:

            command_str1 = command_str + '\n'
            print(command_str1)
            connection.sendall(command_str1)

            data = ''
            while True:
                read = connection.recv(buffer_size)
                data += read
                print(data)
                if read.endswith(delimiter):
                    break
        except Exception:
            return []
        finally:
            connection.shutdown(2)
            connection.close()
            connection = None

        parser = ReponseParser(data)
        return parser.execute()

        # except Exception:
        #     return []



if __name__ == '__main__':
    command = 'get statistics.by_node_name.modem_143-BE.received_packets'
    a = SocketMetricsCollector()
    a.execute('127.0.0.1',10210,command)