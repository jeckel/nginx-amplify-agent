#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import traceback
import platform

distname, distversion, __ = platform.linux_distribution(full_distribution_name=False)
is_centos_6 = distname.lower() == 'centos' and distversion.split('.')[0] == '6'

import amplify

amplify_path = '/'.join(amplify.__file__.split('/')[:-1])
sys.path.insert(0, amplify_path)

from gevent import monkey

if is_centos_6:
    monkey.patch_all(socket=False, ssl=False, select=False)
else:
    monkey.patch_all()

from optparse import OptionParser, Option

from amplify.agent.common.util import configreader

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Andrew Alexeev",
    "Mike Belov",
    "Andrei Belov",
    "Oleg Mamontov",
    "Ivan Poluyanov",
    "Grant Hulegaard",
    "Arie van Luttikhuizen",
    "Igor Meleshchenko",
    "Eugene Morozov",
    "Jason Thigpen",
    "Alexander Shchukin",
    "Clayton Lowell",
    "Paul McGuire",
    "Raymond Lau"
]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


def test_configuration_and_enviroment(config, pid, wait_for_cloud):
    return configreader.test(config, pid, wait_for_cloud)


usage = "usage: %prog [start|stop|configtest] [options]"

option_list = (
    Option(
        '--config',
        action='store',
        dest='config',
        type='string',
        help='path to the config file',
        default=None,
    ),
    Option(
        '--pid',
        action='store',
        dest='pid',
        type='string',
        help='path to the pid file',
        default=None,
    ),
    Option(
        '--foreground',
        action='store_true',
        dest='foreground',
        help='do not daemonize, run in foreground',
        default=False,
    ),
    Option(
        '--log',
        action='store',
        dest='log',
        type='string',
        help='path to the log file',
        default=None,
    ),
)

parser = OptionParser(usage, option_list=option_list)
(options, args) = parser.parse_args()


if __name__ == '__main__':
    try:
        from setproctitle import setproctitle
        setproctitle('amplify-agent')
    except ImportError:
        pass

    try:
        action = sys.argv[1]
        if action not in ('start', 'stop', 'configtest', 'debug'):
            raise IndexError
    except IndexError:
        print("Invalid action or no action supplied\n")
        parser.print_help()
        sys.exit(1)

    # check config before start
    if action in ('configtest', 'debug', 'start'):
        wait_for_cloud = True if action == 'start' else False

        rc = test_configuration_and_enviroment(
            options.config,
            options.pid,
            wait_for_cloud
        )
        print("")

        if action == 'configtest' or rc:
            sys.exit(rc)

    # setup the context
    debug_mode = action == 'debug'
    try:
        from amplify.agent.common.context import context
        context.setup(
            app='agent',
            config_file=options.config,
            pid_file=options.pid,
            log_file=options.log,
            debug=debug_mode
        )
    except:
        import traceback
        print(traceback.format_exc(sys.exc_traceback))

    # run the agent
    try:
        from amplify.agent.supervisor import Supervisor
        supervisor = Supervisor(
            foreground=options.foreground,
            debug=debug_mode
        )

        if options.foreground or (debug_mode and options.log):
            supervisor.run()
        else:
            from amplify.agent.common.runner import Runner
            daemon_runner = Runner(supervisor)
            daemon_runner.do_action()
    except:
        context.default_log.error('uncaught exception during run time', exc_info=True)
        print(traceback.format_exc(sys.exc_traceback))
