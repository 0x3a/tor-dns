#!/usr/bin/env python

import os
import sys
import zmq
import argparse
import datetime
import struct
import hashlib
import ConfigParser
import collections

from models import Base, OnionAddress

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Session = sessionmaker()

def get_onion_page_title(onion):
    # Taken from http://unix.stackexchange.com/questions/103252/how-do-i-get-a-websites-title-using-command-line/103253#103253
    cmd = "torsocks wget -qO- '{}.onion' | perl -l -0777 -ne 'print $1 if /<title.*?>\s*(.*?)\s*<\/title/si'".format(onion)
    
    page_title = ""
    page_title = os.popen(cmd).read()

    # Lazy decoding
    try:
        page_title = page_title.decode('utf-8')
    except:
        print '[!] Cannot decode page title for \'{}.onion\''.format(onion)
    page_title = None

    try:
        page_title = page_title.decode('mac-cyrillic')
    except:
        print '[!] Cannot decode page title for \'{}.onion\''.format(onion)
        page_title = None


    if page_title:
        return page_title.rstrip()
    else:
        return None

def start_receiver(port, host, dbfile, grab_title):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    connect_str = "tcp://%s:%s" % (host, port)

    print '[+] ---- onion.watch importer connecting to publisher at %s ----' % connect_str
    socket.connect(connect_str)
    topicfilter = "101010"
    socket.setsockopt(zmq.SUBSCRIBE, topicfilter)

    engine = create_engine('sqlite:///%s' % dbfile, echo=False)
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)

    print '[+] ---- connected to onion publisher, awaiting messages ---'

    session = Session()
    while True:
        data = socket.recv()
        topic, messagedata = data.split()

        lsplit = messagedata.split('|')
        if len(lsplit) != 2:
            print '[+] Incorrect data received: ', messagedata
            continue
        else:
            print '[+] Received new request: ', messagedata

        
        parsed_date = datetime.datetime.fromtimestamp(float(lsplit[0])/1000.)

        address = lsplit[1]
        onion_address = None

        try:
            onion_address = session.query(OnionAddress).filter(OnionAddress.address == address).one()
            session.commit()
        except:
            pass

        if onion_address:
            onion_address.count += 1
            if onion_address.last_seen < parsed_date:
                onion_address.last_seen = parsed_date

            if (parsed_date - onion_address.last_seen).days >= 1 and grab_title:
                print '[+] Obtaining page title for: {}.onion'.format(address)
                onion_address.website_title = get_onion_page_title(address)

            session.commit()

            print '[+] Updated {}.onion'.format(address)
        else:
            onion_address = OnionAddress()
            onion_address.address = address
            onion_address.count += 1
            onion_address.first_seen = parsed_date
            onion_address.last_seen = parsed_date
            onion_address.website_title = None

            if grab_title:
                print '[+] Obtaining page title for: {}.onion'.format(address)
                onion_address.website_title = get_onion_page_title(address)

            session.add(onion_address)
            session.commit()

            print '[+] Added {}.onion'.format(address)

def main():
    defaults = dict(
        address = '127.0.0.1',
        port = 5556,
        dbfile = "onion.db",
        title = True
    )

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.set_defaults(**defaults)

    parser.add_argument('-a', '--address', help="address to connect on")
    parser.add_argument('-p', '--port', help="port to connect on")
    parser.add_argument('-d', '--dbfile', help="SQLite database filename to save results in")
    parser.add_argument('-t', '--title', help="Sets a flag to grab page titles from hidden services")
    args = parser.parse_args()

    start_receiver(port=args.port, host=args.address, dbfile=args.dbfile, grab_title=args.title)

if __name__ == '__main__':
    sys.exit(main())
