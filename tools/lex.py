#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import json

# make amplify libs available
script_location = os.path.abspath(os.path.expanduser(__file__))
agent_repo_path = os.path.dirname(os.path.dirname(script_location))
sys.path.append(agent_repo_path)

from amplify.agent.objects.nginx.config.amplify_parser.lex import lex_file

__author__ = 'Arie van Luttikhuizen'
__copyright__ = 'Copyright (C) Nginx, Inc. All rights reserved.'
__maintainer__ = 'Arie van Luttikhuizen'
__email__ = 'arie@nginx.com'


def parse_args():
    from argparse import ArgumentParser

    # create parser and parse arguments
    parser = ArgumentParser(description='Lexes tokens of an NGINX config file')
    parser.add_argument('filename', help='NGINX config to lex tokens from')
    parser.add_argument('-n', '--line-numbers', action='store_true', help='include line numbers in json dump')
    parser.add_argument('-i', '--indent', type=int, default=None, metavar='num', help='number of spaces to indent output')
    args = parser.parse_args()

    # prepare filename argument
    args.filename = os.path.expanduser(args.filename)
    args.filename = os.path.abspath(args.filename)
    if not os.path.isfile(args.filename):
        parser.error('filename: No such file or directory')

    return args


def main():
    args = parse_args()

    # use no-space separators if not indenting for a dense json dump
    separators = (',', ':') if args.indent is None else (', ', ': ')

    tokens = []
    for token, lineno in lex_file(args.filename):
        token = token.decode('string_escape')
        tokens.append((token, lineno) if args.line_numbers else token)

    print json.dumps(tokens, indent=args.indent, separators=separators, sort_keys=True)


if __name__ == '__main__':
    main()
