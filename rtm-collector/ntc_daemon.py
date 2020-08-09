#DIALOG VERSION: 2.2.1
import argparse
import logging
import requests
import time
from telegrafpy import TMetric
import ntc_tools
import os
from multiprocessing import Queue
import threading
import math

def run(args, fn_read):
    influx_url = 'http://{0}:{1}/write?db={2}'.format(args.host, args.port, args.database)
    logging.info('streaming data to {0}'.format(influx_url))
    series = []
    transfer_thread = None
    stop_event = None
    queue = Queue()

    # Align interval start on polling time boundary
    current_tm = time.time()
    polling_tm = ntc_tools.get_polling_time(args.interval)
    interval_elapsed = current_tm - polling_tm
    # use ceil of remaining time to avoid starting cycle in last millis of previous interval
    time.sleep(math.ceil(get_interval_remaining_time(args.interval, interval_elapsed)))
    # if fallible is set to True, the collector will crash when an error is encountered. The default is False which will log an error and continue in the standard loop without exiting

    while True:
        tm_start = time.time()
        tm_timestamp = ntc_tools.get_polling_time(args.interval)
        logging.log(15, "{0} start tick".format(tm_start))

        if args.fallible:
            result = fn_read(args)
        else:
            try:
                result = fn_read(args)
                series = [metric for metric in result]
            except Exception as e:
                logging.exception('An error occurred during collection: {0}'.format(str(e)))

        logging.log(15, "{0} result collection finished, start waiting for transfer thread to become available".format(time.time()))

        #wait for the previous transfer thread to finish
        tm_transfer_wait = 0
        if transfer_thread is not None:
            tm_transfer_wait_start = time.time()
            transfer_thread.join(get_interval_remaining_time(args.interval, time.time()-tm_start))
            if transfer_thread.is_alive():
                logging.error("Transfer time exceeds allotted time of interval, stopping transfer thread")
                stop_event.set()
            transfer_thread = None
            tm_transfer_wait_stop = time.time()
            tm_transfer_wait = tm_transfer_wait_stop-tm_transfer_wait_start

        logging.log(15, "{0} transfer thread is available".format(time.time()))

        tm_transfer = 0
        if not queue.empty():
            tm_transfer = queue.get()

        logging.log(15, "{0} popped transfer time from queue, starting transfer thread".format(time.time()))

        if len(series) > 0:
            stop_event = threading.Event()
            transfer_thread = threading.Thread(target=mt_transfer, args=(stop_event, influx_url, series, queue, ))
            transfer_thread.start()

        logging.log(15, "{0} started transfer thread, starting script stats".format(time.time()))

        tm_stop = time.time()

        script_stats = get_script_stats(args, tm_start, tm_stop, tm_transfer, tm_transfer_wait)
        logging.log(15, "{0} collected script stats, transferring".format(time.time()))
        transfer(influx_url, script_stats.format())
        logging.log(15, "{0} transferred script stats, end of tick".format(time.time()))

        tm_total_elapsed = float(time.time() - tm_start)

        if tm_total_elapsed > args.interval:
            logging.warning('processing metrics took longer than {0}s (total processing time {1}s)'.format(args.interval, tm_total_elapsed))
        else:
            #recalculate tm_total_elapsed to improve precision
            tm_total_elapsed = float(time.time() - tm_timestamp)

            wait = get_interval_remaining_time(args.interval, tm_total_elapsed)
            # math.ceil => prefer overshooting interval by few ms to prevent 30s difference between timestamp & collection time
            time.sleep(math.ceil(wait))


def get_interval_remaining_time(interval, elapsed):
    remaining_tm = float(interval) - float(elapsed)
    while(remaining_tm < 0):
        remaining_tm = remaining_tm + float(interval)
    return remaining_tm


def get_script_stats(args, tm_start, tm_stop, tm_transfer, tm_transfer_wait):
    #this is an intermediate solution to quickly get the satnet_if to add as a hps-tag to the app.rtm_collector measurement
    #however, this should later be refactored (in short: make use of a NtcCollector base class with easy accessible basic variables like satnet_if & tm that can be used easily in ntc_daemon)
    tags = {}
    if os.path.exists(ntc_tools.ntc_active_if()):
        satnet_if = ntc_tools.read_single_line(ntc_tools.ntc_active_if())
        tags = { 'hps': satnet_if, 'host': ntc_tools.get_host_name() }
    else:
        #in case of the tcs collector script, satnet_if is in the ntc_active_if param.
        if ntc_tools.ntc_active_if_name() in args.prov:
            satnet_if = ntc_tools.get_config(args.prov, 'ntc_daemon', ntc_tools.ntc_active_if_name())
            tags = { 'hps': satnet_if, 'host': ntc_tools.get_host_name() }

    return TMetric('app.rtm_collector', tm_start, tags, { 'collection_time': (tm_stop - tm_start), 'transfer_time': tm_transfer, 'transfer_wait_time': tm_transfer_wait })


def transfer(influx_url, data):
    try:
        logging.debug("posting data {0} to url {1}".format(data, influx_url))
        requests.post(influx_url, data=data, headers={'content-type': 'application/octet-stream'}, timeout=5)
    except Exception as e:
        logging.error('streaming data to {0} failed w/ exception {1}'.format(influx_url, e.message))


def mt_transfer(stop_event, influx_url, series, queue):
    start = time.time()

    #testing has pointed out throtling towards telegraf_extmon is necessary to avoid drops in data towards influxdb => balancing inptut & output
    #standard batch size of 300 series seems workable w/ 4000 terminals (resulting about 114 runs with a batch size of 300).
    #Lowering the batchsize will increases the amount of runs and the transfer time will exceed 10s
    #transfer time will increase slightly
    batch_size = 300
    #calculate the amount of batches to be created
    #math ceil is used to avoid an amount of batches of 0 (should the amount of series collected be below 300)
    runs = int(math.ceil(len(series) / float(batch_size)))
    data = [series[i * batch_size: (i * batch_size) + batch_size] for i in range(runs)]
    for batch in data:
        if stop_event.is_set():
            logging.error("Transfer thread received stop event, aborting thread, dropping remaining data")
            break
        commands = '\n'.join([metric.format() for metric in batch])
        transfer(influx_url, commands)

    stop = time.time()
    logging.debug("transfer thread time: {0}".format(stop-start))
    queue.put(stop - start)