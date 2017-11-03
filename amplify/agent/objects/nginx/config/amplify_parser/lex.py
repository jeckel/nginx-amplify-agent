# -*- coding: utf-8 -*-
import codecs
import contextlib
import cStringIO
import itertools

from errors import NgxParserSyntaxError

__author__ = 'Arie van Luttikhuizen'
__copyright__ = 'Copyright (C) Nginx, Inc. All rights reserved.'
__maintainer__ = 'Arie van Luttikhuizen'
__email__ = 'arie@nginx.com'


def _iterescape(iterable):
    it = iter(iterable)
    for char in it:
        if char == '\\':
            char = char + next(it)
        yield char


def _iterlinecount(iterable):
    it = iter(iterable)
    lineno = 1
    for char in it:
        if char.endswith('\n'):
            lineno += 1
        yield (char, lineno)


def _lex_file_object(file_obj):
    """
    Generates token tuples from an nginx config file (or file-like) object.

    :param file_obj: file - file or file-like object to read from
    :yields: (str, int) - (token, lineno) tuples
    """
    token = ''  # the token buffer
    token_line = 0  # the line the token starts on

    it = itertools.chain.from_iterable(file_obj)
    it = _iterescape(it)  # treat escaped characters differently
    it = _iterlinecount(it)  # count the number of newline characters

    for char, lineno in it:
        # handle whitespace
        if char.isspace():
            # if token complete yield it and reset token buffer
            if token:
                yield (token, token_line)
                token = ''

            # disregard until char isn't a whitespace character
            while char.isspace():
                char, lineno = next(it)

        # if starting comment then disregard until EOL
        if not token and char == '#':
            while not char.endswith('\n'):  # don't escape newlines
                char, lineno = next(it)
            continue

        if not token:
            token_line = lineno

        # handle parameter expansion syntax (ex: "${var[@]}")
        if token and token[-1] == '$' and char == '{':
            while token[-1] != '}' and not char.isspace():
                token += char
                char, lineno = next(it)

        # if a quote is found, add the whole string to the token buffer
        if char in ('"', "'"):
            if token:
                yield (token, token_line)
                token = ''

            quote = char
            char, lineno = next(it)
            while char != quote:
                token += quote if char == '\\' + quote else char
                char, lineno = next(it)

            yield (token, token_line)
            token = ''

            continue

        # handle special characters that are treated like full tokens
        if char in ('{', '}', ';'):
            # if token complete yield it and reset token buffer
            if token:
                yield (token, token_line)
                token = ''

            # this character is a full token so yield it now
            yield (char, lineno)
            continue

        # append char to the token buffer
        token += char


def _balance_braces(tokens, filename=None):
    """
    Helper function that raises syntax errors if braces aren't balanced.
    
    :param tokens: iterator - must yields (token, lineno) tuples
    :param filename: str - filename to pass to the exception constructor
    :yields: (str, int) - (token, lineno) tuples
    """
    depth = 0

    for token, lineno in tokens:
        if token == '}':
            depth -= 1
        elif token == '{':
            depth += 1

        # raise error if we ever have more right braces than left
        if depth < 0:
            reason = 'unexpected "}"'
            raise NgxParserSyntaxError(reason, filename, lineno)
        else:
            yield token, lineno

    # raise error if we have less right braces than left at EOF
    if depth > 0:
        reason = 'unexpected end of file, expecting "}"'
        raise NgxParserSyntaxError(reason, filename, lineno)


def lex_file(filename):
    """
    Generates tokens from an nginx config file.
    
    :param filename: str - path of file to lex
    :yields: (str, int) - (token, lineno) tuples
    """
    with codecs.open(filename, encoding='utf-8') as fp:
        it = _lex_file_object(fp)
        it = _balance_braces(it, filename)
        for token, lineno in it:
            yield token, lineno


def lex_string(string):
    """
    Generates tokens from an nginx config snippet.

    :param string: str - nginx config snippet to lex
    :yields: (str, int) - (token, lineno) tuples
    """
    buffer = cStringIO.StringIO(string.encode('utf-8'))
    with contextlib.closing(buffer) as fp:
        it = _lex_file_object(fp)
        it = _balance_braces(it, None)
        for token, lineno in it:
            yield token, lineno
