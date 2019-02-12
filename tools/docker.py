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
        shell_call('cat packages/*/requirements-old-gevent.txt >> docker/%s/requirements.txt' % folder)
    else:
        shell_call('cat packages/*/requirements.txt >> docker/%s/requirements.txt' % folder)

    shell_call('docker build %s -t %s docker/%s' % (add_build_args, name, folder), terminal=True)
    shell_call('rm docker/%s/requirements.txt' % folder)


supported_os = ['ubuntu1604', 'ubuntu1604-plus', 'ubuntu1604-mysql8', 'ubuntu1404', 'ubuntu1404-plus', 'debian8', 'centos6', 'centos7', 'alpine', 'gentoo']

usage = "usage: %prog -h"


def get_comma_separated_args(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))


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
        action='callback',
        callback=get_comma_separated_args,
        dest='os',
        type='string',
        help='OS from %s. Default is %s' % (supported_os, supported_os[0]),
        default=[]
    ),
    Option(
        '--scale',
        action='callback',
        dest='scale',
        callback=get_comma_separated_args,
        type='string',
        help='Number of instances of Agent',
        default=[],
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

        if len(options.os) == 0:  # set default os
            options.os.append(supported_os[0])

        runcmd = 'docker-compose'
        scale_cmd = ''
        for os_name in options.os:
            shell_call('docker-compose -f docker/%s.yml down' % os_name, terminal=True)

            if options.rebuild:
                rebuild('%s' % os_name, 'amplify-agent-%s' % os_name, options.build_args)

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

                runcmd += ' -f docker/{0!s}.yml run agent-{0!s} bash'.format(os_name)
            else:
                scale = 1  # set default scale
                if len(options.scale) != 0:
                    scale = options.scale.pop(0)
                scale_cmd += ' --scale agent-{0!s}={1}'.format(os_name, scale)
                runcmd += ' -f docker/{0!s}.yml'.format(os_name)

        if not options.shell:
            runcmd += ' up' + scale_cmd

    if options.background and not options.shell:
        runcmd += ' -d'

    shell_call(runcmd, terminal=True)
