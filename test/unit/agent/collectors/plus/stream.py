# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.context import context
from amplify.agent.objects.plus.object import NginxStreamObject

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class StreamCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(StreamCollectorTestCase, self).setup_method(method)
        context.plus_cache = None
        context._setup_plus_cache()

    def test_gather_data(self):
        stream = NginxStreamObject(local_name='some_stream', parent_local_id='nginx123', root_uuid='root123')
        stream.plus_status_internal_url_cache = 'test_status'

        # Get the stream collector
        stream_collector = stream.collectors[-1]

        context.plus_cache.put('test_status', (
            {
                u'streams': {
                    u'some_stream': {
                        u'connections': 0,
                        u'discarded': 0,
                        u'processing': 0,
                        u'received': 0,
                        u'sent': 0,
                        u'sessions': {
                            u'2xx': 0,
                            u'4xx': 0,
                            u'5xx': 0,
                            u'total': 0
                        }
                    },
                    u'udp_dns': {
                        u'connections': 0,
                        u'discarded': 0,
                        u'processing': 0,
                        u'received': 0,
                        u'sent': 0,
                        u'sessions': {
                            u'2xx': 0,
                            u'4xx': 0,
                            u'5xx': 0,
                            u'total': 0
                        }
                    }
                }
            },
            1
        ))

        data = stream_collector.gather_data()

        assert_that(data, not_(equal_to([])))
        assert_that(data, has_length(1))

    def test_collect(self):
        stream = NginxStreamObject(local_name='some_stream', parent_local_id='nginx123', root_uuid='root123')
        stream.plus_status_internal_url_cache = 'test_status'

        # Get the stream collector
        stream_collector = stream.collectors[-1]
        assert_that(stream_collector.last_collect, equal_to(None))

        context.plus_cache.put('test_status', (
            {
                u'streams': {
                    u'some_stream': {
                        u'connections': 2,
                        u'discarded': 10,
                        u'processing': 60,
                        u'received': 0,
                        u'sent': 0,
                        u'sessions': {
                            u'2xx': 0,
                            u'4xx': 0,
                            u'5xx': 0,
                            u'total': 0
                        }
                    },
                    u'udp_dns': {
                        u'connections': 0,
                        u'discarded': 1,
                        u'processing': 0,
                        u'received': 0,
                        u'sent': 0,
                        u'sessions': {
                            u'2xx': 0,
                            u'4xx': 0,
                            u'5xx': 0,
                            u'total': 0
                        }
                    }
                }
            },
            1
        ))

        context.plus_cache.put('test_status', (
            {
                u'streams': {
                    u'some_stream': {
                        u'connections': 30,
                        u'discarded': 5,
                        u'processing': 5,
                        u'received': 0,
                        u'sent': 0,
                        u'sessions': {
                            u'2xx': 0,
                            u'4xx': 0,
                            u'5xx': 0,
                            u'total': 0
                        }
                    },
                    u'udp_dns': {
                        u'connections': 0,
                        u'discarded': 2,
                        u'processing': 0,
                        u'received': 0,
                        u'sent': 0,
                        u'sessions': {
                            u'2xx': 0,
                            u'4xx': 0,
                            u'5xx': 0,
                            u'total': 0
                        }
                    }
                }
            },
            2
        ))

        stream_collector.collect()
        assert_that(stream_collector.last_collect, equal_to(2))

        assert_that(stream.statsd.current, not_(has_length(0)))

        assert_that(stream.statsd.current, has_key('counter'))
        counters = stream.statsd.current['counter']

        for key in (
            'plus.stream.bytes_sent',
            'plus.stream.bytes_rcvd',
            'plus.stream.status.2xx',
            'plus.stream.status.4xx',
            'plus.stream.status.5xx',
            'plus.stream.conn.accepted',
        ):
            assert_that(counters, has_key(key))

        assert_that(counters['plus.stream.conn.accepted'][0], equal_to([2, 28]))

        gauges = stream.statsd.current['gauge']
        assert_that(gauges, has_key('plus.stream.conn.active'))
        assert_that(gauges['plus.stream.conn.active'][0], equal_to((1, 60)))
