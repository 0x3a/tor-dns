#!/usr/bin/env python

import zmq
import random
import sys
import time
import subprocess
import datetime
import argparse

epoch = datetime.datetime.utcfromtimestamp(0)
def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0

def start_publisher(host, port, noticefile):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://%s:%s" % (host, port))

    print '[+] ---- onion.watch ZMQ publisher started on tcp://%s:%s ----' % (host, port)

    f = subprocess.Popen(['tail', '-F', noticefile], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print '[+] Tailing notice log \'%s\'' % noticefile
    
    while True:
        line = f.stdout.readline()
        if 'HSDIR_REQUEST' not in line or '|None' in line:
            continue

        lsplit = line.split('|')
        if len(lsplit) != 3:
            continue

        parsed_date = datetime.datetime.strptime(line.split('[')[0] + str(datetime.datetime.now().year), "%b %d  %H:%M:%S.%f %Y")
        address = lsplit[2].rstrip().lstrip()

        topic = 101010
        message = "%d %f|%s" % (topic, unix_time_millis(parsed_date), address)
        print '[+] Sending new request: ' + message
        socket.send(message)

def main():
    defaults = dict(
        listen = '127.0.0.1',
        port = 5556,
        noticelog = "notice.log"
    )

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.set_defaults(**defaults)

    parser.add_argument('-l', '--listen', help="address to listen on")
    parser.add_argument('-p', '--port', help="port to listen on")
    parser.add_argument('-n', '--noticelog', help="notice logfile from the Tor client to tail")
    args = parser.parse_args()

    start_publisher(port=args.port, host=args.listen, noticefile=args.noticelog)

if __name__ == "__main__":
    sys.exit(main())
