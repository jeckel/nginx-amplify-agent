# -*- coding: utf-8 -*-
import glob
import os

from lex import lex_file
from analyze import analyze, enter_block_ctx
from errors import NgxParserDirectiveError

__author__ = 'Arie van Luttikhuizen'
__copyright__ = 'Copyright (C) Nginx, Inc. All rights reserved.'
__maintainer__ = 'Arie van Luttikhuizen'
__email__ = 'arie@nginx.com'


# TODO: raise special errors for invalid "if" args
def _prepare_if_args(stmt):
    """
    Removes parentheses from an "if" directive's arguments.

    :param stmt: dict - an nginx config statement dict
    """
    args = stmt['args']
    if args and args[0].startswith('(') and args[-1].endswith(')'):
        args[0] = args[0][1:].lstrip()
        args[-1] = args[-1][:-1].rstrip()
        start = int(not args[0])
        end = len(args) - int(not args[-1])
        args[:] = args[start:end]


def parse_file(filename, onerror=None, catch_errors=False):
    """
    Parses an nginx config file and returns a nested dict payload.

    :param filename: str - abspath of the main nginx config file
    :param onerror: function - optional callback that handles parsing errors
    :param catch_errors: bool - whether to collect multiple errors per file
    :return: dict - a payload of parsing results
    """
    config_dir = os.path.dirname(filename)

    payload = {
        'status': 'ok',
        'errors': [],
        'config': [],
    }

    includes = []  # stores (config filename, config context) tuples
    included = set()

    def _handle_error(parsing, e):
        """
        Helper function that adds representaions of an error to the payload.
        
        :param parsing: dict - the dict being constructed when error occurred
        :param e: exception - the exception that was raised
        """
        message = e.strerror if hasattr(e, 'strerror') else e.message
        line = getattr(e, 'lineno', None)

        parsing_error = {'error': message, 'line': line}
        payload_error = dict(parsing_error, file=parsing['file'])
        if onerror is not None:
            payload_error['callback'] = onerror(e)

        parsing['status'] = 'failed'
        parsing['errors'].append(parsing_error)

        payload['status'] = 'failed'
        payload['errors'].append(payload_error)

    def _nginx_glob(pattern):
        """
        Helper function for mimicking how nginx handles globbing.

        If the pattern is not an absolute path, one will be constructed using
        the main nginx config file's directory.

        If the pattern is just a file path with no "magic" (e.g. *, ?, [...]),
        then it'll always return the path even if the file does not exist.

        :param pattern: str - a path pattern that can have "magic" characters
        :return: list - a list of absolute file paths
        """
        if not os.path.isabs(pattern):
            pattern = os.path.join(config_dir, pattern)
        if not glob.has_magic(pattern):
            return [pattern]
        else:
            return glob.glob(pattern)

    def _parse(parsing, tokens, ctx=(), consume=False):
        """
        Helper function that recursively parses nginx config contexts.
        
        :param parsing: dict - the dict that's currently being constructed
        :param tokens: iterable - a stream of lexed (token, lineno) tuples
        :param ctx: tuple - the current nginx context (see analyze.py)
        :param consume: bool - if True just consume the upcoming context
        :returns: list - a list of nginx config statement dicts
        """
        fname = parsing['file']
        parsed = []

        # parse recursively by pulling from a flat stream of tokens
        for token, lineno in tokens:
            # we are parsing a block, so break if it's closing
            if token == '}':
                break

            # if we are consuming, then just continue until end of context
            if consume:
                # if we find a block inside this context, consume it too
                if token == '{':
                    _parse(parsing, tokens, consume=True)
                continue

            # the first token should always(?) be an nginx directive
            stmt = {
                'directive': token,
                'line': lineno,
                'args': []
            }

            # parse arguments by reading tokens
            args = stmt['args']
            token, __ = next(tokens)  # disregard line numbers of args
            while token not in ('{', ';'):
                stmt['args'].append(token)
                token, __ = next(tokens)

            # prepare arguments
            if stmt['directive'] == 'if':
                _prepare_if_args(stmt)

            try:
                # raise errors if this statement is invalid
                analyze(fname, stmt, token, ctx)
            except NgxParserDirectiveError as e:
                if catch_errors:
                    _handle_error(parsing, e)

                    # if it was a block but shouldn't have been then consume
                    if e.strerror.endswith(' is not terminated by ";"'):
                        _parse(parsing, tokens, consume=True)

                    # keep on parsin'
                    continue
                else:
                    raise e

            # add "includes" to the payload if this is an include statement
            if stmt['directive'] == 'include':
                stmt['includes'] = _nginx_glob(args[0])
                includes.extend((f, ctx) for f in stmt['includes'])

            # if this statement terminated with '{' then it is a block
            if token == '{':
                inner = enter_block_ctx(stmt, ctx)  # get context for this block
                stmt['block'] = _parse(parsing, tokens, ctx=inner)

            parsed.append(stmt)

        return parsed

    # start with the main nginx config file/context
    includes.append((filename, ()))

    # the includes list grows as "include" directives are found in _parse
    for fname, ctx in includes:
        # the included set keeps files from being parsed twice
        # TODO: handle cases where files are included from multiple contexts
        if fname not in included:
            included.add(fname)
            tokens = lex_file(fname)
            parsing = {
                'file': fname,
                'errors': [],
                'parsed': [],
                'status': 'ok'
            }
            try:
                parsing['parsed'] = _parse(parsing, tokens, ctx=ctx)
            except Exception as e:
                _handle_error(parsing, e)

            payload['config'].append(parsing)

    return payload
