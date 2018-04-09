# -*- coding: utf-8 -*-
import copy
import fnmatch
import glob
import os
import re
import sys

import scandir

from amplify.agent.common.context import context
from crossplane.parser import parse as parse_file
from crossplane.errors import NgxParserDirectiveError
from crossplane.lexer import _iterescape

__author__ = 'Arie van Luttikhuizen'
__copyright__ = 'Copyright (C) Nginx, Inc. All rights reserved.'
__maintainer__ = 'Arie van Luttikhuizen'
__email__ = 'arie@nginx.com'

INCLUDE_ONLY_RE = re.compile(r'(?:^|[;{}])\s*(include)\s+([\'"]?)([^#]*?)\2\s*?(?=;)')
INCLUDE_CERT_RE = re.compile(r'(?:^|[;{}])\s*(include|ssl_certificate)\s+([\'"]?)([^#]*?)\2\s*?(?=;)')

ARGDICT_DIRECTIVES = frozenset([
    'log_format'
])

ALWAYS_PACK_DIRECTIVES = frozenset([
    'include'
])

ALWAYS_PACK_BLOCKS = frozenset([
    'server'
])

NEVER_PACK_DIRECTIVES = frozenset()

NEVER_PACK_BLOCKS = frozenset([
    'http',
    'events',
    'types'
])

IGNORED_DIRECTIVES = frozenset([
    'ssl_certificate_key',
    'ssl_client_certificate',
    'ssl_password_file',
    'ssl_stapling_file',
    'ssl_trusted_certificate',
    'auth_basic_user_file',
    'secure_link_secret'
])


def _is_always_packed(cmd, is_block=None):
    if is_block is None:
        return cmd in ALWAYS_PACK_BLOCKS or cmd in ALWAYS_PACK_DIRECTIVES
    return cmd in (ALWAYS_PACK_BLOCKS if is_block else ALWAYS_PACK_DIRECTIVES)


def _is_never_packed(cmd, is_block=None):
    if is_block is None:
        return cmd in NEVER_PACK_BLOCKS or cmd in NEVER_PACK_DIRECTIVES
    return cmd in (NEVER_PACK_BLOCKS if is_block else NEVER_PACK_DIRECTIVES)


def get_filesystem_info(path):
    size, mtime, permissions = 0, 0, '0000'
    try:
        info = os.stat(path)
        size = info.st_size
        mtime = int(info.st_mtime)
        permissions = oct(info.st_mode & 0777).zfill(4)
    except Exception as e:
        exc_cls = e.__class__.__name__
        message = 'failed to stat %s do to %s' % (path, exc_cls)
        context.log.debug(message, exc_info=True)
    finally:
        return {'size': size, 'mtime': mtime, 'permissions': permissions}


def _enquote(arg):
    arg = str(arg.encode('utf-8'))
    if not arg or any(char.isspace() for char in _iterescape(arg)):
        return repr(arg).decode('string_escape')
    else:
        return arg


def argstring(stmt):
    if not stmt['args']:
        return ''
    elif stmt['directive'] in ARGDICT_DIRECTIVES:
        return ''.join(x.encode('utf-8').decode('string_escape') for x in stmt['args'][1:])
    else:
        return ' '.join(map(_enquote, stmt['args']))


def store_directive(block, stmt, value):
    cmd = stmt['directive']
    if cmd in ARGDICT_DIRECTIVES:
        key = stmt['args'][0]
        block.setdefault(cmd, {})[key] = value
    elif 'block' in stmt and stmt['args']:
        key = argstring(stmt)
        block.setdefault(cmd, {})[key] = value
    elif _is_always_packed(cmd, is_block='block' in stmt):
        block.setdefault(cmd, []).append(value)
    elif _is_never_packed(cmd, is_block='block' in stmt) or cmd not in block:
        block[cmd] = value
    elif isinstance(block[cmd], list):
        block[cmd].append(value)
    else:
        block[cmd] = [block[cmd], value]


def merge_blocks(a, b):
    for cmd, value in b.iteritems():
        if cmd in ARGDICT_DIRECTIVES:
            a.setdefault(cmd, {}).update(value)
        elif _is_always_packed(cmd):
            a.setdefault(cmd, []).extend(value)
        elif _is_never_packed(cmd) or cmd not in a:
            a[cmd] = value
        elif isinstance(a[cmd], dict) and isinstance(value, dict):
            a[cmd].update(value)
        elif isinstance(a[cmd], list) and isinstance(value, list):
            a[cmd].extend(value)
        elif isinstance(a[cmd], list):
            a[cmd].append(value)
        elif isinstance(value, list):
            a[cmd] = [a[cmd]] + value
        else:
            a[cmd] = [a[cmd], value]


def _fnmatch_pattern(names, pttn):
    if glob.has_magic(pttn):
        return fnmatch.filter(names, pttn)
    else:
        return [pttn] if pttn in names else []


def _iglob_pattern(pattern):
    if glob.has_magic(pattern):
        for path in glob.iglob(pattern):
            yield path
    else:
        yield pattern


def _getline(filename, lineno):
    with open(filename) as fp:
        for i, line in enumerate(fp, start=1):
            if i == lineno:
                return line.rstrip('\r\n')


class NginxConfigParser(object):
    def __init__(self, filename='/etc/nginx/nginx.conf'):
        self.filename = filename
        self.directory = self._dirname(filename)

        self.files = {}
        self.directories = {}
        self.directory_map = {}

        self.errors = []
        self.broken_files = {}
        self.broken_directories = {}

        self.index = []  # list of directive locations (file, lineno)
        self.tree = {}

        self.includes = []
        self.ssl_certificates = []

        self._converted_cache = {}
        self._parsed_cache = {}
        self._file_order = {}

    def _abspath(self, path):
        if not os.path.isabs(path):
            path = os.path.join(self.directory, path)
        return os.path.normpath(path)

    def _dirname(self, path):
        return os.path.dirname(path) + '/'

    def _handle_error(self, path, e, is_dir=False, exc_info=True, what='read'):
        """
        Stores and logs errors raised by reading and parsing the nginx config
        
        :param path: str - the absolute path of the file or directory
        :param e: Exception - the exception that was raised
        :param is_dir: bool - whether the path is for a directory
        :param exc_info: True or (exc_type, exc_value, exc_traceback)
        :param what: str - what action caused the error (used for logging)
        """
        exc_cls = e.__class__.__name__
        exc_msg = e.strerror if hasattr(e, 'strerror') else e.message
        message = 'failed to %s %s due to: %s' % (what, path, exc_cls)
        self.errors.append(message)
        if is_dir:
            self.broken_directories[path] = '%s: %s' % (exc_cls, exc_msg)
            context.log.debug(message, exc_info=exc_info)
        else:
            self.broken_files[path] = '%s: %s' % (exc_cls, exc_msg)
            context.log.error(message)

            if isinstance(e, NgxParserDirectiveError):
                line = _getline(e.filename, e.lineno)
                context.log.debug('line where error was raised: %r' % line)

            context.log.debug('additional info:', exc_info=exc_info)

    def _add_directory(self, dirname, check=False):
        if dirname not in self.directories:
            self.directories[dirname] = get_filesystem_info(dirname)
            if check:
                try:
                    scandir.scandir(dirname)
                except Exception as e:
                    self._handle_error(dirname, e, is_dir=True)

    def _add_file(self, filename):
        if filename not in self.files:
            dirname = self._dirname(filename)
            self._add_directory(dirname, check=True)
            try:
                info = get_filesystem_info(filename)
                info['index'] = len(self.files)
                info['lines'] = open(filename).read().count('\n')
                self.files[filename] = info
            except Exception as e:
                self._handle_error(filename, e, is_dir=False)

        if filename in self.files:
            return self.files[filename]['index']

    def _add_index(self, filename, lineno):
        file_index = self._add_file(filename)
        self.index.append((file_index, lineno))
        return len(self.index) - 1

    def _scan_path_pattern(self, pattern):
        """Similar to glob.iglob, except it saves directory errors"""

        # just yield the file if it's a regular boring path with no magic
        magic = glob.magic_check.search(pattern)
        if magic is None:
            yield pattern
            return

        # find the deepest path before the first magic part
        anchor, after = glob.magic_check.split(pattern, 1)
        anchor, start = anchor.rsplit('/', 1)

        offset = anchor.count('/') + 1
        anchor = anchor or '/'

        # get all of the following path parts (>=1 will have magic)
        after = start + magic.group(0) + after
        parts = after.split('/')

        # used to handle directory errors when walking filesystem
        def onerror(e):
            dirname = e.filename + '/'
            if dirname not in self.directories:
                self.directories[dirname] = get_filesystem_info(dirname)
                self._handle_error(dirname, e, is_dir=True)

        # walk the filesystem to collect file paths (and directory errors)
        it = scandir.walk(anchor, followlinks=True, onerror=onerror)
        for root, dirs, files in it:
            # get the index of the current path part to use
            index = (root != '/') + root.count('/') - offset

            if index > len(parts) - 1:
                # must've followed a recursive link so go no deeper
                dirs[:] = []
            elif index < len(parts) - 1:
                # determine which directories to walk into next
                dirs[:] = _fnmatch_pattern(dirs, parts[index])
            else:
                # this is the last part, so yield from matching files
                for f in _fnmatch_pattern(files, parts[index]):
                    yield os.path.join(root, f)

                # yield from matching directories too
                for d in _fnmatch_pattern(dirs, parts[index]):
                    yield os.path.join(root, d) + '/'

    def _convert(self, filename, ngx_ctx=None):
        """
        Convert a new style payload to the old 'dense' style payload
        
        :param filename: str - name of the file
        :param ngx_ctx: dict - block from block directive to convert
        :return: dict - the converted block payload
        """
        # pause for a bit if this is taking up too much cpu
        context.check_and_limit_cpu_consumption()

        if ngx_ctx is not None:
            skip_cache = True  # because we're parsing a block context
        elif filename in self._converted_cache:
            cached = self._converted_cache[filename]
            return copy.deepcopy(cached)
        elif filename in self._parsed_cache:
            ngx_ctx = self._parsed_cache[filename]
            skip_cache = False  # because this is the top context for a file
        else:
            return {}  # this file must've been empty

        block = {}

        for stmt in ngx_ctx:
            # ignore certain directives for security reasons
            if stmt['directive'] in IGNORED_DIRECTIVES:
                continue

            # get the directive's value
            if 'block' in stmt:
                value = self._convert(filename, stmt['block'])
            else:
                value = argstring(stmt)

            # ignore access/error log directives if they use nginx variables
            if stmt['directive'] in ('access_log', 'error_log'):
                if not value or ('$' in value and ' if=$' not in value):
                    continue

            # add the (file name, line number) tuple to self.index
            index = self._add_index(filename, stmt['line'])

            # add the (directive value, index index) tuple to the block
            store_directive(block, stmt, (value, index))

            if stmt['directive'] == 'include':
                value = self._abspath(value)
                if value not in self.includes:
                    self.includes.append(value)

                # add the included directives to the current block
                for index in stmt['includes']:
                    fname = self._file_order[index]
                    merge_blocks(block, self._convert(fname))

            elif stmt['directive'] == 'ssl_certificate' and value:
                # skip if value uses nginx variables other than if
                if value and ('$' not in value or ' if=$' in value):
                    value = self._abspath(value)
                    if value not in self.ssl_certificates:
                        self.ssl_certificates.append(value)

        # we cache converted junk by file, so skip if we just parsed a block
        if not skip_cache:
            self._converted_cache[filename] = copy.deepcopy(block)

        return block

    def parse(self):
        # clear results from the previous run
        self.files = {}
        self.directories = {}

        # clear some bits and pieces from previous run
        self.broken_files = {}
        self.broken_directories = {}
        self.includes = []
        self.ssl_certificates = []
        try:
            # use the new parser to parse the nginx config
            get_exc_info = lambda e: sys.exc_info()
            payload = parse_file(self.filename, onerror=get_exc_info, catch_errors=True)

            for error in payload['errors']:
                path = error['file']
                exc_info = error['callback']
                try:
                    # these error types are handled by this script already
                    if not isinstance(exc_info[1], (OSError, IOError)):
                        self._handle_error(path, exc_info[1], exc_info=exc_info, what='parse')
                        self._add_file(path)
                finally:
                    # this speeds things up by deleting traceback, see python docs
                    del exc_info

            for index, config in enumerate(payload['config']):
                path = config['file']
                self._file_order[index] = path
                if config['parsed']:
                    self._parsed_cache[path] = config['parsed']
                    self._add_file(path)

            # convert the parsed payload into our dense payload structure
            self._add_file(self.filename)
            self.tree = self._convert(self.filename)

            # use found include patterns to check for os errors
            for pattern in self.includes:
                for filename in self._scan_path_pattern(pattern):
                    self._add_file(filename)

            # add directories that only contain ssl cert files
            for cert in self.ssl_certificates:
                dirname = self._dirname(cert)
                self._add_directory(dirname, check=True)

            # construct self.directory_map
            dirmap = self.directory_map

            # start with directories
            for dirname, info in self.directories.iteritems():
                dirmap[dirname] = {'info': info, 'files': {}}

            for dirname, error in self.broken_directories.iteritems():
                dirmap.setdefault(dirname, {'info': {}, 'files': {}})
                dirmap[dirname]['error'] = error

            # then do files
            for filename, info in self.files.iteritems():
                dirname = self._dirname(filename)
                dirmap[dirname]['files'][filename] = {'info': info}

            for filename, error in self.broken_files.iteritems():
                dirname = self._dirname(filename)
                dirmap[dirname]['files'].setdefault(filename, {'info': {}})
                dirmap[dirname]['files'][filename]['error'] = error
        finally:
            # clear the converted and parsed caches
            self._converted_cache = {}
            self._parsed_cache = {}
            self._file_order = {}

    def simplify(self):
        """
        Returns self.tree without the "self.index index" tuples

        :return: dict - self.tree without index positions
        """
        def _simplify(tree):
            if isinstance(tree, dict):
                return dict((k, _simplify(v)) for k, v in tree.iteritems())
            elif isinstance(tree, list):
                return map(_simplify, tree)
            elif isinstance(tree, tuple):
                return _simplify(tree[0])
            return tree

        return _simplify(self.tree)

    def get_structure(self, include_ssl_certs=False):
        """
        Collects included files, ssl cert files, and their directories and
        then returns them as dicts with mtimes, sizes, and permissions

        :param include_ssl_certs: bool - include ssl certs  or not
        :return: (dict, dict) - files, directories
        """
        files = {}

        if include_ssl_certs:
            regex = INCLUDE_CERT_RE
            has_directive = lambda line: 'include' in line or 'ssl_certificate' in line
        else:
            regex = INCLUDE_ONLY_RE
            has_directive = lambda line: 'include' in line

        def _skim_file(filename):
            """
            Recursively skims nginx configs for include and ssl_certificate
            directives, yielding paths of the files they reference on the way
            """
            if filename in files:
                return

            yield filename
            try:
                # search each line for include or ssl_certificate directives
                with open(filename) as lines:
                    for line in lines:
                        if not has_directive(line):
                            continue

                        for match in regex.finditer(line):
                            if not match:
                                continue

                            file_pattern = self._abspath(match.group(3))

                            # add directory but don't use self._scan_path_pattern
                            # because we don't need to collect directory errors
                            dir_pattern = self._dirname(file_pattern)
                            for path in _iglob_pattern(dir_pattern):
                                self._add_directory(path, check=True)

                            # yield from matching files using _iglob_pattern
                            for path in _iglob_pattern(file_pattern):
                                if match.group(1) == 'include':
                                    for p in _skim_file(path):
                                        yield p
                                else:
                                    yield path
            except Exception as e:
                self._handle_error(filename, e, is_dir=False)

        # collect file names and get mtimes, sizes, and permissions for them
        for fname in _skim_file(self.filename):
            files[fname] = get_filesystem_info(fname)

        return files, self.directories
