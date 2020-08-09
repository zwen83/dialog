#DIALOG VERSION: 2.2.2

import logging
import ntc_tools
import time
import ntc_daemon

def main(default_config,
         default_port,
         register,
         read,
         name):
    try:
        args = ntc_tools.parse_config()
        '''
        {'fallible': False, 
        'src_port': 10210, 
        'log': '/var/log/rtm-collector/rtm-collector.log', 
        'database': 'telegraf', 
        'loglevel': 'INFO', 
        'prov': {'terminals': '/var/ntc-active-hps/rtmc/rtn_terminals', 
        'rtn_link': '/var/ntc-active-hps/rtmc/rtn_link.yaml', 
        'ntc-active-hps': '/var/run/ntc-active-hps', 
        'multicast': '/var/ntc-active-hps/rtmc/multicastcircuits'}, 
        'interval': 30, 
        'host': 'localhost', 
        'mode': 'RUNONCE', 
        'port': 8186, 
        'src_host': '127.0.0.1'}
        
        '''


        ntc_tools.configure_logging(args.log, args.loglevel, name)

        config = ntc_tools.get_default_args(default_config, args.prov)
        '''
        {'ntc-active-hps': '/var/run/ntc-active-hps', 'terminals': 
        '/var/ntc-active-hps/rtmc/rtn_terminals', 
        'multicast': '/var/ntc-active-hps/rtmc/multicastcircuits', 
        'rtn_link': '/var/ntc-active-hps/rtmc/rtn_link.yaml'}
        
        '''


        args.src_port = ntc_tools.get_default_args(default_port, args.src_port)
        '''
        10210
        '''
        logging.info('registering configuration: {0}'.format(config))
        register(config)

        run_mode = ntc_tools.get_run_mode(args.mode)
        if run_mode == ntc_tools.RunMode.DAEMON or run_mode == ntc_tools.RunMode.MOCK:
            ntc_daemon.run(args, read)
        else:
            start = time.time()
            result = read(args)

            '''
            <itertools.chain object at 0x200a990>

            '''

            count = 0

            for metric in result:
                print(metric.format())
                count = count + 1
            stop = time.time()

            print('collected {0} metrics in {1}s'.format(count, str(stop - start)))
    except Exception as ex:
        logging.exception('An error occurred during collector execution: {0}'.format(str(ex)))
        #the collector exits when this occurs, but an error is still logged. Multiple exits result in a failover.
