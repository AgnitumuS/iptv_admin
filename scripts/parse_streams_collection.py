#!/usr/bin/env python3
import argparse
import os
import sys
from mongoengine import connect

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

PROJECT_NAME = 'parse_streams_collection'

from app.common.stream.entry import IStream

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=PROJECT_NAME, usage='%(prog)s [options]')
    parser.add_argument('--mongo_uri', help='MongoDB credentials', default='mongodb://localhost:27017/iptv')

    argv = parser.parse_args()

    mongo = connect(host=argv.mongo_uri)
    if mongo:
        streams = IStream.objects()
        f = open("out.m3u", "w")
        f.write('#EXTM3U\n')
        idx = 0
        for stream in streams:
            f.write(stream.generate_input_playlist(False))
        f.close()
