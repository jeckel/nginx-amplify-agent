#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from optparse import OptionParser, Option

from builders.util import shell_call, color_print


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


def rebuild(folder, name, build_args):
    add_build_args = ''
    if len(build_args) > 0:
        for build_arg in build_args:
            add_build_args += (' --build-arg %s' % build_arg)

    if folder == 'centos6':
        shell_call('cat packages/*/requirements-old-gevent >> docker/%s/requirements' % folder)
    else:
        shell_call('cat packages/*/requirements >> docker/%s/requirements' % folder)
    if folder == 'ubuntu1604-controller':
        shell_call('docker build -t %s -f docker/%s/Dockerfile .' % (name, folder), terminal=True)
    else:
        shell_call('docker build %s -t %s docker/%s' % (add_build_args, name, folder), terminal=True)
    shell_call('rm docker/%s/requirements' % folder)


supported_os = ['ubuntu1604', 'ubuntu1604-plus', 'ubuntu1604-controller', 'ubuntu1604-mysql8', 'ubuntu1404', 'ubuntu1404-plus', 'ubuntu1004', 'debian8', 'centos6', 'centos7', 'alpine']

usage = "usage: %prog -h"

option_list = (
    Option(
        '--rebuild',
        action='store_true',
        dest='rebuild',
        help='Rebuild before run (False by default)',
        default=False,
    ),
    Option(
        '--build-arg',
        action='append',
        dest='build_args',
        help='Build arguments for docker build',
        default=[],
        type='str',
    ),
    Option(
        '--drop',
        action='store_true',
        dest='drop',
        help='Drop everything before run (False by default)',
        default=False,
    ),
    Option(
        '--background',
        action='store_true',
        dest='background',
        help='Run in background (False by default)',
        default=False,
    ),
    Option(
        '--shell',
        action='store_true',
        dest='shell',
        help='Get shell access',
        default=False,
    ),
    Option(
        '--os',
        action='store',
        dest='os',
        type='string',
        help='OS from %s. Default is %s' % (supported_os, supported_os[0]),
        default=supported_os[0],
    ),
    Option(
        '--all',
        action='store_true',
        dest='all',
        help='Runs all agent images! Watch for CPU!',
        default=False
    ),
)

parser = OptionParser(usage, option_list=option_list)
(options, args) = parser.parse_args()

if __name__ == '__main__':
    shell_call('find . -name "*.pyc" -type f -delete')

    if options.drop:
        shell_call('docker stop $(docker ps -a -q)')
        shell_call('docker rm $(docker ps -a -q)')

    if options.all:
        shell_call('docker-compose -f docker/agents.yml down', terminal=True)

        if options.rebuild:
            for osname in supported_os:
                rebuild('%s' % osname, 'amplify-agent-%s' % osname, options.build_args)

        runcmd = 'docker-compose -f docker/agents.yml up'
    else:
        shell_call('docker-compose -f docker/%s.yml down' % options.os, terminal=True)

        if options.rebuild:
            rebuild('%s' % options.os, 'amplify-agent-%s' % options.os, options.build_args)

        if options.shell:
            rows, columns = os.popen('stty size', 'r').read().split()
            color_print("\n= USEFUL COMMANDS =" + "="*(int(columns)-20))
            for helper in (
                "service nginx start",
                "service php7.0-fpm start",
                "service mysql start",
                "python /amplify/nginx-amplify-agent.py start --config=/amplify/etc/agent.conf.development",
                "python /amplify/nginx-amplify-agent.py stop --config=/amplify/etc/agent.conf.development"
            ):
                color_print(helper, color='yellow')
            color_print("="*int(columns)+"\n")

            runcmd = 'docker-compose -f docker/%s.yml run agent bash' % options.os
        else:
            runcmd = 'docker-compose -f docker/%s.yml up' % options.os

    if options.background and not options.shell:
        runcmd += ' -d'

    shell_call(runcmd, terminal=True)
