#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys
from traceback import format_exception

# make amplify libs available
script_location = os.path.abspath(os.path.expanduser(__file__))
agent_repo_path = os.path.dirname(os.path.dirname(script_location))
sys.path.append(agent_repo_path)

from amplify.agent.objects.nginx.config.amplify_parser.parse import parse_file

__author__ = 'Arie van Luttikhuizen'
__copyright__ = 'Copyright (C) Nginx, Inc. All rights reserved.'
__maintainer__ = 'Arie van Luttikhuizen'
__email__ = 'arie@nginx.com'


def tb_onerror(e):
    etype, value, tb = sys.exc_info()
    try:
        return format_exception(etype, value, tb, 10)
    finally:
        del etype, value, tb


def parse_args():
    from argparse import ArgumentParser

    # create parser and parse arguments
    parser = ArgumentParser(description='Print the new style config parser payload for a given nginx config')
    parser.add_argument('filename')
    parser.add_argument('--no-catch', action='store_false', dest='catch', help='only collect first error in file')
    parser.add_argument('--use-onerror', action='store_true', help='include tracebacks in config errors')
    parser.add_argument('-i', '--indent', type=int, default=4, metavar='N', help='number of spaces to indent output')
    args = parser.parse_args()

    # prepare filename argument
    args.filename = os.path.expanduser(args.filename)
    args.filename = os.path.abspath(args.filename)
    if not os.path.isfile(args.filename):
        parser.error('filename: No such file or directory')

    return args


def main():
    args = parse_args()

    kwargs = {'catch_errors': args.catch}
    if args.use_onerror:
        kwargs['onerror'] = tb_onerror

    payload = parse_file(args.filename, **kwargs)
    if args.indent > 0:
        print json.dumps(payload, indent=args.indent, sort_keys=True)
    else:
        print json.dumps(payload, sort_keys=True)


if __name__ == '__main__':
    main()
