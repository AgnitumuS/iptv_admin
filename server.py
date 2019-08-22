#!/usr/bin/env python3

from app import app, servers_manager
import argparse
from gevent.pywsgi import WSGIServer
import gevent

PROJECT_NAME = 'iptv_admin'
HOST = '0.0.0.0'
PORT = 8080


def servers_refresh():
    servers_manager.refresh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=PROJECT_NAME, usage='%(prog)s [options]')
    parser.add_argument('--port', help='port (default: {0})'.format(PORT), default=PORT)
    parser.add_argument('--host', help='host (default: {0})'.format(HOST), default=HOST)
    argv = parser.parse_args()

    http_server = WSGIServer((argv.host, argv.port), app)
    srv_greenlet = gevent.spawn(http_server.serve_forever)
    alarm_greenlet = gevent.spawn(servers_refresh)

    try:
        gevent.joinall([srv_greenlet, alarm_greenlet])
    except KeyboardInterrupt:
        servers_manager.stop()
        http_server.stop()
