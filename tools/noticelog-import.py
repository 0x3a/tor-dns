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

def start_import(noticefile, logyear, dbfile, grab_title):
    engine = create_engine('sqlite:///%s' % dbfile, echo=False)
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)

    notice_log = open(noticefile, 'r')

    session = Session()
    for line in notice_log.readlines():

        if 'HSDIR_REQUEST' not in line or '|None' in line:
            continue

        lsplit = line.split('|')
        if len(lsplit) != 3:
            continue

        parsed_date = datetime.datetime.strptime(line.split('[')[0] + logyear, "%b %d  %H:%M:%S.%f %Y")
        address = lsplit[2].rstrip()
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
        noticefile = 'notice.log',
        logyear = datetime.datetime.now().year,
        dbfile = "onion.db",
        title=True
    )

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.set_defaults(**defaults)

    parser.add_argument('-n', '--noticefile', help="Tor notice log to parse")
    parser.add_argument('-y', '--logyear', help="Year the notice log was generated in (notice log itself doesnt specify this)")
    parser.add_argument('-d', '--dbfile', help="SQLite database filename to save results in")
    parser.add_argument('-t', '--title', help="Sets a flag to grab page titles from hidden services")
    args = parser.parse_args()

    start_import(noticefile=args.noticefile, logyear=args.logyear, dbfile=args.dbfile, grab_title=args.title)

if __name__ == '__main__':
    sys.exit(main())
