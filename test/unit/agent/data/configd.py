# -*-# -*- coding: utf-8 -*-
import time

from hamcrest import *

from amplify.agent.objects.system.object import SystemObject
from test.base import BaseTestCase

__author__ = 'Arie van Luttikhuizen'
__copyright__ = 'Copyright (C) Nginx, Inc. All rights reserved.'
__license__ = ''
__maintainer__ = 'Arie van Luttikhuizen'
__email__ = 'arie@nginx.com'


class ConfigdClientTestCase(BaseTestCase):
    def test_flush_resends_configs(self):
        obj = SystemObject(hostname='foo', uuid='bar')

        cfg1 = dict(a=1, b=2, c=3)
        cfg2 = dict(d=4, e=5, f=6)
        cfg3 = dict(g=7, h=8, i=9)

        # check that if no config has been stored no config gets sent
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))

        # check that a config gets sent once one is stored
        obj.configd.config(cfg1, 'abc123')
        assert_that(obj.configd.flush(resend_wait_time=2), has_entries(config={'data': cfg1, 'checksum': 'abc123'}))
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))

        # check that sleeping longer than resend_wait_time results in a previous config being sent on flush
        time.sleep(3)
        assert_that(obj.configd.flush(resend_wait_time=2), has_entries(config={'data': cfg1, 'checksum': 'abc123'}))
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
        time.sleep(1)  # less than resend_wait_time
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
        time.sleep(1)  # less than resend_wait_time
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
        time.sleep(1)  # more than resend_wait_time

        # check that after another period of resend_wait_seconds, the previously sent config gets sent again
        assert_that(obj.configd.flush(resend_wait_time=2), has_entries(config={'data': cfg1, 'checksum': 'abc123'}))
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))

        # check that updating a config resets time to wait until flush in the new config getting sent on flush
        obj.configd.config(cfg2, 'def456')
        assert_that(obj.configd.flush(resend_wait_time=2), has_entries(config={'data': cfg2, 'checksum': 'def456'}))
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
        time.sleep(1)  # less than resend_wait_time
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
        time.sleep(1)  # less than resend_wait_time
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
        time.sleep(1)  # more than resend_wait_time
        assert_that(obj.configd.flush(resend_wait_time=2), has_entries(config={'data': cfg2, 'checksum': 'def456'}))
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))

        # the same should hold true when you update a config a bunch of times before flushing
        obj.configd.config(cfg3, 'ghi789')
        obj.configd.config(cfg1, 'abc123')
        obj.configd.config(cfg2, 'def456')
        assert_that(obj.configd.flush(resend_wait_time=2), has_entries(config={'data': cfg2, 'checksum': 'def456'}))
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
        time.sleep(1)  # less than resend_wait_time
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
        time.sleep(1)  # less than resend_wait_time
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
        time.sleep(1)  # more than resend_wait_time
        assert_that(obj.configd.flush(resend_wait_time=2), has_entries(config={'data': cfg2, 'checksum': 'def456'}))
        assert_that(obj.configd.flush(resend_wait_time=2), not_(has_key('config')))
