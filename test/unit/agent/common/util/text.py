# -*- coding: utf-8 -*-
import pprint
from collections import defaultdict

from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.util.text import (
    decompose_format, parse_line, parse_line_split
)


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


COMBINED_FORMAT = '$remote_addr - $remote_user [$time_local] "$request" ' + \
                  '$status $body_bytes_sent "$http_referer" "$http_user_agent"'


class UtilTextTestCase(BaseTestCase):
    def test_decompose_format_regular(self):
        keys, trie, non_key_patterns, first_value_is_key = decompose_format(
            COMBINED_FORMAT, full=True
        )
        assert_that(keys, not_none())
        assert_that(trie, not_none())
        assert_that(non_key_patterns, not_none())
        assert_that(first_value_is_key, equal_to(True))

        assert_that(keys, equal_to([
            'remote_addr', 'remote_user', 'time_local', 'request', 'status',
            'body_bytes_sent', 'http_referer', 'http_user_agent'
        ]))
        assert_that(non_key_patterns, equal_to([
            ' - ', ' [', '] "', '" ', ' ', ' "', '" "', '"'
        ]))

    def test_decompose_format_different(self):
        log_format = '$remote_addr - $remote_user [$time_local] ' + \
                     '"$request" $status $body_bytes_sent "$http_referer" ' + \
                     '"$http_user_agent" rt=$request_time ' + \
                     'ut="$upstream_response_time" cs=$upstream_cache_status'

        keys, trie, non_key_patterns, first_value_is_key = decompose_format(log_format, full=True)
        assert_that(keys, not_none())
        assert_that(trie, not_none())
        assert_that(non_key_patterns, not_none())
        assert_that(first_value_is_key, equal_to(True))

        assert_that(keys, equal_to([
            'remote_addr', 'remote_user', 'time_local', 'request', 'status',
            'body_bytes_sent', 'http_referer', 'http_user_agent',
            'request_time', 'upstream_response_time', 'upstream_cache_status'
        ]))

        assert_that(non_key_patterns, equal_to([
            ' - ', ' [', '] "', '" ', ' ', ' "', '" "', '" rt=', ' ut="',
            '" cs='
        ]))

    def test_parse_line(self):
        keys, trie = decompose_format(COMBINED_FORMAT)
        line = '127.0.0.1 - - [02/Jul/2015:14:49:48 +0000] "GET /basic_status HTTP/1.1" 200 110 "-" ' + \
               '"python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic"'

        results = parse_line(line, keys=keys, trie=trie)
        assert_that(results, not_none())
        
        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['http_user_agent'], equal_to(
            'python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic'
        ))

    def test_parse_line_split(self):
        keys, _, non_key_patterns, first_value_is_key = decompose_format(COMBINED_FORMAT, full=True)
        line = '127.0.0.1 - - [02/Jul/2015:14:49:48 +0000] "GET /basic_status HTTP/1.1" 200 110 "-" ' + \
               '"python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic"'

        results = parse_line_split(
            line,
            keys=keys,
            non_key_patterns=non_key_patterns,
            first_value_is_key=first_value_is_key
        )
        assert_that(results, not_none())

        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['http_user_agent'], equal_to(
            'python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic'
        ))

    def test_parse_line_non_standard_http_method(self):
        keys, trie = decompose_format(COMBINED_FORMAT)
        line = '127.0.0.1 - - [02/Jul/2015:14:49:48 +0000] "PROPFIND /basic_status HTTP/1.1" 200 110 "-" ' + \
               '"python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic"'

        results = parse_line(line, keys=keys, trie=trie)
        assert_that(results, not_none())
        
        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['http_user_agent'], equal_to(
            'python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic'
        ))

    def test_parse_line_split_non_standard_http_method(self):
        keys, _, non_key_patterns, first_value_is_key = decompose_format(
            COMBINED_FORMAT, full=True
        )
        line = '127.0.0.1 - - [02/Jul/2015:14:49:48 +0000] "PROPFIND /basic_status HTTP/1.1" 200 110 "-" ' + \
               '"python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic"'

        results = parse_line_split(
            line,
            keys=keys,
            non_key_patterns=non_key_patterns,
            first_value_is_key=first_value_is_key
        )
        assert_that(results, not_none())
        
        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['http_user_agent'], equal_to(
            'python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic'
        ))

    def test_parse_line_upstream_log_format(self):
        log_format = '$remote_addr - $remote_user [$time_local] ' + \
                     '"$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" ' + \
                     'rt=$request_time ut="$upstream_response_time" cs=$upstream_cache_status'

        keys, trie = decompose_format(log_format)
        line = \
            '1.2.3.4 - - [22/Jan/2010:19:34:21 +0300] "GET /foo/ HTTP/1.1" 200 11078 ' + \
            '"http://www.rambler.ru/" "Mozilla/5.0 (Windows; U; Windows NT 5.1" rt=0.010 ut="2.001, 0.345" cs=MISS'

        results = parse_line(line, keys=keys, trie=trie)
        assert_that(results, not_none())
        
        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['upstream_cache_status'], equal_to('MISS'))

        # check some complicated values
        assert_that(results['request_time'], equal_to('0.010'))
        assert_that(results['upstream_response_time'], equal_to('2.001, 0.345'))

    def test_parse_line_split_upstream_log_format(self):
        log_format = '$remote_addr - $remote_user [$time_local] ' + \
                     '"$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" ' + \
                     'rt=$request_time ut="$upstream_response_time" cs=$upstream_cache_status'

        keys, _, non_key_patterns, first_value_is_key = decompose_format(log_format, full=True)
        line = \
            '1.2.3.4 - - [22/Jan/2010:19:34:21 +0300] "GET /foo/ HTTP/1.1" 200 11078 ' + \
            '"http://www.rambler.ru/" "Mozilla/5.0 (Windows; U; Windows NT 5.1" rt=0.010 ut="2.001, 0.345" cs=MISS'

        results = parse_line_split(
            line,
            keys=keys,
            non_key_patterns=non_key_patterns,
            first_value_is_key=first_value_is_key
        )
        assert_that(results, not_none())
        
        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['upstream_cache_status'], equal_to('MISS'))

        # check some complicated values
        assert_that(results['request_time'], equal_to('0.010'))
        assert_that(results['upstream_response_time'], equal_to('2.001, 0.345'))

    def test_parse_line_upstream_log_format_empty_upstreams(self):
        log_format ='$remote_addr - $remote_user [$time_local] ' + \
                     '"$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" ' + \
                     'rt=$request_time cs=$upstream_cache_status ut="$upstream_response_time"'

        keys, trie = decompose_format(log_format)
        line = \
            '1.2.3.4 - - [22/Jan/2010:19:34:21 +0300] "GET /foo/ HTTP/1.1" 200 11078 ' + \
            '"http://www.rambler.ru/" "Mozilla/5.0 (Windows; U; Windows NT 5.1" rt=0.010 cs=- ut="-"'

        results = parse_line(line, keys=keys, trie=trie)
        assert_that(results, not_none())
        
        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['upstream_response_time'], equal_to('-'))
        
        assert_that(results['upstream_cache_status'], equal_to('-'))

    def test_parse_line_split_upstream_log_format_empty_upstreams(self):
        log_format ='$remote_addr - $remote_user [$time_local] ' + \
                     '"$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" ' + \
                     'rt=$request_time cs=$upstream_cache_status ut="$upstream_response_time"'

        keys, _, non_key_patterns, first_value_is_key = decompose_format(
            log_format, full=True
        )
        line = \
            '1.2.3.4 - - [22/Jan/2010:19:34:21 +0300] "GET /foo/ HTTP/1.1" 200 11078 ' + \
            '"http://www.rambler.ru/" "Mozilla/5.0 (Windows; U; Windows NT 5.1" rt=0.010 cs=- ut="-"'

        results = parse_line_split(
            line,
            keys=keys,
            non_key_patterns=non_key_patterns,
            first_value_is_key=first_value_is_key
        )
        assert_that(results, not_none())
        
        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['upstream_response_time'], equal_to('-'))
        
        assert_that(results['upstream_cache_status'], equal_to('-'))
        
    def test_parse_line_upstream_log_format_part_empty_upstreams(self):
        log_format = '$remote_addr - $remote_user [$time_local] ' + \
                     '"$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" ' + \
                     'rt=$request_time ut="$upstream_response_time" cs=$upstream_cache_status'

        keys, trie = decompose_format(log_format)
        line = \
            '1.2.3.4 - - [22/Jan/2010:19:34:21 +0300] "GET /foo/ HTTP/1.1" 200 11078 ' + \
            '"http://www.rambler.ru/" "Mozilla/5.0 (Windows; U; Windows NT 5.1" rt=0.010 ut="-" cs=MISS'

        results = parse_line(line, keys=keys, trie=trie)
        assert_that(results, not_none())
        
        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['upstream_cache_status'], equal_to('MISS'))

    def test_parse_line_split_upstream_log_format_part_empty_upstreams(self):
        log_format = '$remote_addr - $remote_user [$time_local] ' + \
                     '"$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" ' + \
                     'rt=$request_time ut="$upstream_response_time" cs=$upstream_cache_status'

        keys, _, non_key_patterns, first_value_is_key = decompose_format(log_format, full=True)
        line = \
            '1.2.3.4 - - [22/Jan/2010:19:34:21 +0300] "GET /foo/ HTTP/1.1" 200 11078 ' + \
            '"http://www.rambler.ru/" "Mozilla/5.0 (Windows; U; Windows NT 5.1" rt=0.010 ut="-" cs=MISS'

        results = parse_line_split(
            line,
            keys=keys,
            non_key_patterns=non_key_patterns,
            first_value_is_key=first_value_is_key
        )
        assert_that(results, not_none())
        
        for key in keys:
            assert_that(results, has_item(key))
            assert_that(results[key], not_none())

        # check the last value to make sure complete parse
        assert_that(results['upstream_cache_status'], equal_to('MISS'))

