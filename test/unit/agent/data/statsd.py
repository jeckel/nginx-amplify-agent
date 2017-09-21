# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase
from amplify.agent.data.statsd import StatsdClient

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class StatsdClientTestCase(BaseTestCase):

    def test_incr_negative_amount(self):
        client = StatsdClient()

        client.incr('test_positive', value=100)
        assert_that(len(client.current['counter']), equal_to(1))  # check that we saved the value

        client.incr('test_negative', value=-200)
        assert_that(len(client.current['counter']), equal_to(1))  # we did't add negative metric
