# -*- coding: utf-8 -*-
import re

from hamcrest import *

from amplify.agent.objects.nginx.filters import Filter
from test.base import BaseTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class FiltersTestCase(BaseTestCase):
    def test_init(self):
        filtr = Filter(
            filter_rule_id='1',
            metric='http.something',
            data=[
                ['logname', '~', 'foo.txt'],
                ['$request_method', '~', 'post'],
                ['$request_uri', '~', '.*\.gif'],
                ['$status', '!~', '200']
            ]
        )
        assert_that(filtr.filter_rule_id, equal_to('1'))
        assert_that(filtr.metric, equal_to('http.something'))
        assert_that(filtr.filename, equal_to('foo.txt'))

        assert_that('logname', not_(is_in(filtr.data)))
        assert_that(filtr.data['request_method'], equal_to(re.compile("POST")))
        assert_that(filtr.data['request_uri'], equal_to(re.compile(".*\.gif")))
        assert_that(filtr.data['status'], equal_to(re.compile("200")))

        assert_that('logname', not_(is_in(filtr._negated_conditions)))
        assert_that(filtr._negated_conditions['request_method'], equal_to(False))
        assert_that(filtr._negated_conditions['request_uri'], equal_to(False))
        assert_that(filtr._negated_conditions['status'], equal_to(True))

    def test_init_without_filename(self):
        filtr = Filter(
            filter_rule_id='1',
            metric='http.something',
            data=[
                ['$request_method', '~', 'post'],
                ['$request_uri', '~', '*.gif']
            ]
        )
        assert_that(filtr.filename, equal_to(None))

    def test_empty(self):
        filtr = Filter(
            filter_rule_id='1',
            metric='http.something',
            data=[]
        )
        assert_that(filtr.empty, equal_to(True))

    def test_filematch(self):
        filtr = Filter(
            filter_rule_id='1',
            metric='http.something',
            data=[
                ['logname', '~', 'foo.txt']
            ]
        )

        assert_that(filtr.matchfile('foo.txt'), equal_to(True))
        assert_that(filtr.matchfile('foo.log'), equal_to(False))

        filtr = Filter(
            filter_rule_id='1',
            metric='http.something',
            data=[
                ['logname', '!~', 'foo.txt']
            ]
        )

        assert_that(filtr.matchfile('foo.txt'), equal_to(False))
        assert_that(filtr.matchfile('foo.log'), equal_to(True))

        filtr = Filter(
            filter_rule_id='1',
            metric='http.something',
            data=[
                ['$request_method', '~', 'post'],
                ['$request_uri', '~', '.*\.gif'],
                ['$status', '!~', '200']            ]
        )

        assert_that(filtr.matchfile('foo.txt'), equal_to(True))
        assert_that(filtr.matchfile('foo.log'), equal_to(True))
