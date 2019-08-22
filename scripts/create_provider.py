#!/usr/bin/env python3
import argparse
import os
import sys
from mongoengine import connect

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.home.entry import ProviderUser

PROJECT_NAME = 'create_provider'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=PROJECT_NAME, usage='%(prog)s [options]')
    parser.add_argument('--mongo_uri', help='MongoDB credentials', default='mongodb://localhost:27017/iptv')
    parser.add_argument('--email', help='Provider email')
    parser.add_argument('--password', help='Provider password')
    parser.add_argument('--country', help='Provider country', default='US')

    argv = parser.parse_args()
    email = argv.email
    password = argv.password

    mongo = connect(host=argv.mongo_uri)
    if not mongo:
        sys.exit(1)

    new_user = ProviderUser.make_provider(email=email, password=password, country=argv.country)
    new_user.status = ProviderUser.Status.ACTIVE
    new_user.save()
    print('Successfully created provider email: {0}, password: {1}'.format(email, password))
