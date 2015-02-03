#!/usr/bin/python

import os
import sys
import argparse
import requests
import yaml
import json

args = None


class Foreman(object):
    def __init__(self,
                 foreman_endpoint=None,
                 foreman_user=None,
                 foreman_password=None):

        self.foreman_endpoint = foreman_endpoint
        self.foreman_user = foreman_user
        self.foreman_password = foreman_password

        self.hostgroups = {}
        self.hgid = {}
        self.hosts = {}

        self.get_hostgroups()
        self.get_hosts()

    def get(self, url):
        if self.foreman_user:
            auth = requests.auth.HTTPBasicAuth(
                self.foreman_user,
                self.foreman_password)
        else:
            auth = None

        r = requests.get(url, auth=auth)
        r.raise_for_status()

        return r

    def get_hostgroups(self):
        url = '%s/api/hostgroups' % self.foreman_endpoint
        r = self.get(url)

        for hg in r.json():
            this = {
                'hosts': [],
                'vars': hg['hostgroup']['parameters'],
            }
            self.hostgroups[hg['hostgroup']['name']] = this
            self.hgid[hg['hostgroup']['id']] = this

        self.hostgroups['__none__'] = {
            'hosts': [],
            'vars': {},
        }

    def get_hosts(self):
        url = '%s/api/hosts' % self.foreman_endpoint
        r = self.get(url)

        for host in r.json():
            hgid = host['host']['hostgroup_id']
            if hgid is None:
                hg = self.hostgroups['__none__']
            else:
                hg = self.hgid[hgid]

            hg['hosts'].append(host['host']['name'])
            self.hosts[host['host']['name']] = hg


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--config', '-f',
                   default='foreman.yaml')
    p.add_argument('--list',
                   action='store_true')
    p.add_argument('--host')
    p.add_argument('--hosts', '--hostnames',
                   action='store_true')
    p.add_argument('--groups', '--hostgroups',
                   action='store_true')
    return p.parse_args()


def main():
    args = parse_args()
    with open(args.config) as fd:
        conf = yaml.load(fd)

    if 'foreman' not in conf:
        conf['foreman'] = {}

    foreman = Foreman(
        conf['foreman'].get('url', 'http://localhost'),
        conf['foreman'].get('username'),
        conf['foreman'].get('password')
    )

    if args.host:
        print json.dumps(foreman.hosts[args.host]['vars'],
                         indent=2)
    elif args.list:
        print json.dumps(foreman.hostgroups,
                         indent=2)
    elif args.hosts:
        print '\n'.join(foreman.hosts.keys())
    else:
        print '\n'.join(foreman.hostgroups.keys())


if __name__ == '__main__':
    main()

