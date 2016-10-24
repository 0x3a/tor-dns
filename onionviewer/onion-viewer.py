#!/usr/bin/env python

import sys
import argparse
import datetime

from flask import Flask, request, url_for, abort, render_template
from models import Base, OnionAddress
from flask.ext.sqlalchemy import SQLAlchemy, Pagination
from sqlalchemy import func, desc, asc
from flask.ext.babel import Babel

app = Flask(__name__)
app.config.from_object(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///onion.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

app.config["BABEL_DEFAULT_LOCALE"] = "en_US"
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
babel = Babel(app)

@app.before_first_request
def setup():
    Base.metadata.create_all(bind=db.engine)

@app.route('/', defaults={'page':1})
@app.route('/page/<int:page>')
def index(page):
    db_query = db.session.query(OnionAddress)

    total = None
    per_page = request.args.get("limit", "")
    if not per_page:
        per_page = 10

    per_page = int(per_page)

    q = request.args.get("q", "")
    if q:
        q = "%{}%".format(q)
        db_query = db_query.filter(OnionAddress.address.ilike(q))

    query_order = None
    qo = request.args.get("order", "")
    if qo:
        query_order = qo

        if qo == "address_desc":
            db_query = db_query.order_by(OnionAddress.address.desc())
        elif qo == "address_asc":
            db_query = db_query.order_by(OnionAddress.address.asc())
        elif qo == "fs_desc":
            db_query = db_query.order_by(OnionAddress.first_seen.desc())
        elif qo == "fs_asc":
            db_query = db_query.order_by(OnionAddress.first_seen.asc())
        elif qo == "ls_desc":
            db_query = db_query.order_by(OnionAddress.last_seen.desc())
        elif qo == "ls_asc":
            db_query = db_query.order_by(OnionAddress.last_seen.asc())
        elif qo == "count_desc":
            db_query = db_query.order_by(OnionAddress.count.desc())
        elif qo == "count_asc":
            db_query = db_query.order_by(OnionAddress.count.asc())
        else:
            db_query = db_query.order_by(OnionAddress.last_seen.desc())
    else:
        db_query = db_query.order_by(OnionAddress.last_seen.desc())
        query_order = "ls_desc";

    total = db_query.count()
    onion_addresses = db_query.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(db_query, page, per_page, total, onion_addresses)

    total_count = db.session.query(OnionAddress).count()

    return render_template('index.html', pagination=pagination, total_count=total_count, query_order=query_order)

@app.route('/search/', defaults={'page':1})
@app.route("/search/<int:page>", methods=["GET", "POST"])
def search(page):
    per_page = 50
    q = request.args.get("q", "")
    q = "%{}%".format(q)
    q = db.session.query(OnionAddress).filter(OnionAddress.address.ilike(q)).order_by(OnionAddress.last_seen.desc())
    total = q.count()
    onion_addresses = q.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(q, page, per_page, total, onion_addresses)
    return render_template("index.html", pagination=pagination, total_count=total)

@app.route("/onion/<address>")
def onion_address(address):
    onion_address = db.session.query(OnionAddress).filter(OnionAddress.address == address).one()

    return render_template('onion_address.html', onion_address=onion_address)

# URL Generation helper from http://flask.pocoo.org/snippets/44/
def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

def main():
    defaults = dict(
        listen = '127.0.0.1',
        port = 8081,
        database = "onion.db"
    )

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.set_defaults(**defaults)

    parser.add_argument('-l', '--listen', help="address to listen on")
    parser.add_argument('-p', '--port', help="port to listen on")
    parser.add_argument('-d', '--database', help="database file")
    args = parser.parse_args()

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % args.database
    db = SQLAlchemy(app)
    
    app.run(port=args.port, host=args.listen, debug=False)

if __name__ == '__main__':
    sys.exit(main())
