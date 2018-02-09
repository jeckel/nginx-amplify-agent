# -*- coding: utf-8 -*-
import re

from amplify.agent.common.context import context
from amplify.agent.common.util.escape import prep_raw


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


REQUEST_RE = re.compile(r'(?P<request_method>[A-Z]+) (?P<request_uri>/.*) (?P<server_protocol>.+)')


class NginxAccessLogParser(object):
    """
    Nginx access log parser
    """
    combined_format = '$remote_addr - $remote_user [$time_local] "$request" ' + \
                      '$status $body_bytes_sent "$http_referer" "$http_user_agent"'

    default_variable = ['.+', str]

    common_variables = {
        'request': ['.+', str],
        'body_bytes_sent': ['\d+', int],
        'bytes_sent': ['\d+', int],
        'connection': ['[\d\s]+', str],
        'connection_requests': ['\d+', int],
        'msec': ['.+', float],
        'pipe': ['[p|\.]', str],
        'request_length': ['\d+', int],
        'request_time': ['.+', str],
        'status': ['\d+', str],
        'server_name': ['.*', str],
        'time_iso8601': ['.+', str],
        'time_local': ['.+', str],
        'upstream_response_time': ['.+', str],
        'upstream_response_length': ['.+', int],
        'upstream_connect_time': ['.+', str],
        'upstream_header_time': ['.+', str],
        'upstream_status': ['.+', str],
        'upstream_cache_status': ['.+', str],
        'gzip_ratio': ['.+', float],
    }

    # TODO: Remove this now semi-unnecessary variable.
    request_variables = {
        'request_method': ['[A-Z]+', str],
        'request_uri': ['/.*', str],
        'server_protocol': ['[\d\.]+', str],
    }

    comma_separated_keys = [
        'upstream_addr',
        'upstream_status'
    ]

    def __init__(self, raw_format=None):
        """
        Takes raw format and generates regex
        :param raw_format: raw log format
        """
        self.raw_format = self.combined_format if raw_format is None else raw_format

        self.keys = []
        self.regex_string = r''
        self.regex = None
        self.separators = []
        self.start_from_separator = False

        # preprocess raw format and if we have trailing spaces in format we should remove them
        self.raw_format = prep_raw(self.raw_format).rstrip()

        current_key = None
        current_separator = None

        def finalize_key():
            """
            Finalizes key:
            1) removes $ and {} from it
            2) adds a regex for the key to the regex_string
            """
            chars_to_remove = ['$', '{', '}']
            plain_key = current_key.translate(None, ''.join(chars_to_remove))

            self.keys.append(plain_key)
            rxp = self.common_variables.get(plain_key, self.default_variable)[0]

            # Handle formats with multiple instances of the same variable.
            var_count = self.keys.count(plain_key)
            if var_count > 1:  # Duplicate variables will be named starting at 2 (var, var2, var3, etc...)
                regex_var_name = '%s_occurance_%s' % (plain_key, var_count)
            else:
                regex_var_name = plain_key
            self.regex_string += '(?P<%s>%s)' % (regex_var_name, rxp)

        char_index = 0
        for char in self.raw_format:
            if current_key:
                if char.isalpha() or char.isdigit() or char == '_' or (char == '{' and current_key == '$'):
                    current_key += char
                elif char == '}':  # the end of ${key} format
                    current_key += char
                    finalize_key()
                else:  # finalize key and start a new one
                    finalize_key()

                    if char == '$':  # if there's a new key - create it
                        current_key = char
                    else:
                        # otherwise - add char to regex
                        current_key = None

                        safe_char = char if (char.isalpha() or char.isdigit()) else '\%s' % char
                        self.regex_string += safe_char

                        if current_separator is not None:
                            current_separator += char
                        else:
                            current_separator = char
            else:
                # if there's no current key
                if char == '$':
                    current_key = char

                    if current_separator is not None:
                        self.separators.append(current_separator)
                        current_separator = None
                else:
                    safe_char = char if (char.isalpha() or char.isdigit()) else '\%s' % char
                    self.regex_string += safe_char

                    if current_separator is not None:
                        current_separator += char
                    else:
                        current_separator = char

                    if char_index == 0:
                        self.start_from_separator = True

            char_index += 1

        # key can be the last element in a string
        if current_key:
            finalize_key()

        # separator also can be the last element in a string
        if current_separator:
            self.separators.append(current_separator)

        self.regex = re.compile(self.regex_string)

        # these two values are used for every line, so let's have them saved
        self.keys_amount = len(self.keys)
        self.separators_amount = len(self.separators)

    def parse(self, line):
        """
        New parse method, that parses a line using separators

        :param line: str line
        :return: dict with parsed info
        """
        result = {'malformed': False}

        key_index = 0
        remainder = line

        for separator_index in xrange(self.separators_amount):
            separator = self.separators[separator_index]
            raw_value, remainder = remainder.split(separator, 1)

            # if a line starts from separator - skip the part before the separator
            if self.start_from_separator and separator_index == 0:
                continue

            # get the key and process the value
            key = self.keys[key_index]
            processed_value = self._process_key_value(key, raw_value)
            if processed_value is not None:
                result[key] = processed_value

            key_index += 1

        # there can be the last value
        if key_index < self.keys_amount:
            key = self.keys[key_index]
            result[key] = self._process_key_value(key, remainder)

        # process request
        if 'request' in result:
            try:
                method, uri, proto = result['request'].split(' ')
                result['request_method'] = method
                result['request_uri'] = uri
                result['server_protocol'] = proto
            except:
                result['malformed'] = True
                method = ''

            is_malformed = not (len(method) >= 3 and method.isupper())
            result['malformed'] = is_malformed

        return result

    def _process_key_value(self, key, raw_value):
        """
        Performs various actions on value according to the key

        :param key: str key
        :param raw_value: str value
        :return: str result or None
        """
        time_var = False

        # get the function, try/except works faster for standard vars
        try:
            func = self.common_variables[key][1]
        except KeyError:
            func = self.default_variable[1]

        # process the value
        try:
            value = func(raw_value)
        except ValueError:
            return 0

        # time variables should be parsed to array of float
        if key.endswith('_time'):
            time_var = True
            # skip empty vars
            if value != '-':
                array_value = []
                for x in value.replace(' ', '').split(','):
                    x = float(x)
                    # workaround for an old nginx bug with time. ask lonerr@ for details
                    if x > 10000000:
                        continue
                    else:
                        array_value.append(x)

                if array_value:
                    return array_value

        # handle comma-separated keys
        if key in self.comma_separated_keys:
            if ',' in value:
                list_value = value.replace(' ', '').split(',')  # remove spaces and split values into list
                return list_value
            else:
                return [value]

        if not time_var:
            return value
