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
                print(key, value, split_metric[len(split_metric)-2], parts[1], parts)
                '''
                ('received_bytes', 
                '60599665',
                 'sit_18074_BE', 
                 'statistics.by_node_name.sit_18074_BE.received_bytes',
                  ['OK:', 'statistics.by_node_name.sit_18074_BE.received_bytes', 'MonotonicIntegerWithUnit', '60599665', 'bytes'])
                '''

                metric = Metric(key, value, split_metric[len(split_metric)-2], parts[1], parts)
                self.append(metric)
                '''
                ('received_bytes', '60599665', 'sit_18074_BE', 'statistics.by_node_name.sit_18074_BE.received_bytes', ['OK:', 'statistics.by_node_name.sit_18074_BE.received_bytes', 'MonotonicIntegerWithUnit', '60599665', 'bytes'])
                ('received_packets', '152955', 'sit_18074_BE', 'statistics.by_node_name.sit_18074_BE.received_packets', ['OK:', 'statistics.by_node_name.sit_18074_BE.received_packets', 'MonotonicIntegerWithUnit', '152955', 'packets'])
                ('received_bytes', '79198526', 'sit_18510_BE', 'statistics.by_node_name.sit_18510_BE.received_bytes', ['OK:', 'statistics.by_node_name.sit_18510_BE.received_bytes', 'MonotonicIntegerWithUnit', '79198526', 'bytes'])
                ('received_packets', '227858', 'sit_18510_BE', 'statistics.by_node_name.sit_18510_BE.received_packets', ['OK:', 'statistics.by_node_name.sit_18510_BE.received_packets', 'MonotonicIntegerWithUnit', '227858', 'packets'])
                ('received_bytes', '9679538646', 'sit_11958_BE', 'statistics.by_node_name.sit_11958_BE.received_bytes', ['OK:', 'statistics.by_node_name.sit_11958_BE.received_bytes', 'MonotonicIntegerWithUnit', '9679538646', 'bytes'])
                ('received_packets', '19501352', 'sit_11958_BE', 'statistics.by_node_name.sit_11958_BE.received_packets', ['OK:', 'statistics.by_node_name.sit_11958_BE.received_packets', 'MonotonicIntegerWithUnit', '19501352', 'packets'])

                '''

    def execute(self):
        lines = self.response.split('\r\n')
        [self.parse(line) for line in lines]
        print(self.metrics)
        '''
        [<metric.Metric instance at 0x1adf9e0>, 
        <metric.Metric instance at 0x1adfa28>, 
        <metric.Metric instance at 0x1adfa70>, 
        <metric.Metric instance at 0x1adfb00>, 
        <metric.Metric instance at 0x1adfb48>, 
        <metric.Metric instance at 0x1adfb90>]

        '''


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
                '''
                
                get statistics.by_node_name.sit_18074_BE.received_bytes
                get statistics.by_node_name.sit_18074_BE.received_packets
                get statistics.by_node_name.sit_18510_BE.received_bytes
                get statistics.by_node_name.sit_18510_BE.received_packets
                get statistics.by_node_name.sit_11958_BE.received_bytes
                get statistics.by_node_name.sit_11958_BE.received_packets

                '''

                connection.sendall(command_str)

                data = ''
                while True:
                    read = connection.recv(buffer_size)


                    data += read
                    '''
                    OK: Connected
                    [on] >
                    OK: Connected
                    [on] >OK: statistics.by_node_name.sit_18074_BE.received_bytes MonotonicIntegerWithUnit 60599665 bytes
                    [on] >OK: statistics.by_node_name.sit_18074_BE.received_packets MonotonicIntegerWithUnit 152955 packets
                    [on] >OK: statistics.by_node_name.sit_18510_BE.received_bytes MonotonicIntegerWithUnit 79198526 bytes
                    [on] >OK: statistics.by_node_name.sit_18510_BE.received_packets MonotonicIntegerWithUnit 227858 packets
                    [on] >OK: statistics.by_node_name.sit_11958_BE.received_bytes MonotonicIntegerWithUnit 9679538646 bytes
                    [on] >OK: statistics.by_node_name.sit_11958_BE.received_packets MonotonicIntegerWithUnit 19501352 packets
                    [on] >[on] >
                    
                    '''
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
