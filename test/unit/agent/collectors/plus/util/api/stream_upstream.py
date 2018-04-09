# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.context import context
from amplify.agent.objects.plus.api import NginxApiStreamUpstreamObject

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class ApiStreamUpstreamCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(ApiStreamUpstreamCollectorTestCase, self).setup_method(method)
        context.plus_cache = None
        context._setup_plus_cache()

    def test_gather_data(self):
        stream_upstream = NginxApiStreamUpstreamObject(
            local_name='backend',
            parent_local_id='nginx123',
            root_uuid='root123'
        )
        stream_upstream.api_internal_url_cache = 'test_api'

        # Get the stream_upstream collector
        stream_upstream_collector = stream_upstream.collectors[-1]

        context.plus_cache.put('test_api', (
            {
                u'stream': {
                    u'upstreams' : {
                        u'backend': {
                            u'peers': [
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 0,
                                    u'name': u'backend1.example.com:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'198.105.254.130:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 5
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 1,
                                    u'name': u'backend1.example.com:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'104.239.207.44:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 5
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 2,
                                    u'name': u'127.0.0.1:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'127.0.0.1:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 1
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 3,
                                    u'name': u'unix:/tmp/backend3',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'unix:/tmp/backend3',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 1
                                }
                            ],
                            u'zombies': 0,
                            u'zone': u'up-backend'
                        }
                    }
                }
            },
            1
        ))

        data = stream_upstream_collector.gather_data()

        assert_that(data, not_(equal_to([])))
        assert_that(data, has_length(1))

    def test_collect(self):
        stream_upstream = NginxApiStreamUpstreamObject(
            local_name='backend',
            parent_local_id='nginx123',
            root_uuid='root123'
        )
        stream_upstream.api_internal_url_cache = 'test_api'

        # Get the stream_upstream collector
        stream_upstream_collector = stream_upstream.collectors[-1]
        assert_that(stream_upstream_collector.last_collect, equal_to(None))

        context.plus_cache.put('test_api', (
            {
                u'stream': {
                    u'upstreams' : {
                        u'backend': {
                            u'peers': [
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 0,
                                    u'name': u'backend1.example.com:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'198.105.254.130:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 5
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 1,
                                    u'name': u'backend1.example.com:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'104.239.207.44:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 5
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 2,
                                    u'name': u'127.0.0.1:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'127.0.0.1:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 1
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 3,
                                    u'name': u'unix:/tmp/backend3',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'unix:/tmp/backend3',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 1
                                }
                            ],
                            u'zombies': 0,
                            u'zone': u'up-backend'
                        }
                    }
                }
            },
            1
        ))

        context.plus_cache.put('test_api', (
            {
                u'stream': {
                    u'upstreams' : {
                        u'backend': {
                            u'peers': [
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 10,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 0,
                                    u'name': u'backend1.example.com:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'198.105.254.130:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 5
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 20,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 1,
                                    u'name': u'backend1.example.com:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'104.239.207.44:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 5
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 30,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 2,
                                    u'name': u'127.0.0.1:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'127.0.0.1:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 1
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 40,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 3,
                                    u'name': u'unix:/tmp/backend3',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'unix:/tmp/backend3',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 1
                                }
                            ],
                            u'zombies': 0,
                            u'zone': u'up-backend'
                        }
                    }
                }
            },
            2
        ))

        stream_upstream_collector.collect()
        assert_that(stream_upstream_collector.last_collect, equal_to(2))

        assert_that(stream_upstream.statsd.current, not_(has_length(0)))

        assert_that(stream_upstream.statsd.current, has_key('counter'))
        counters = stream_upstream.statsd.current['counter']

        for key in (
            'plus.stream.upstream.conn.count', 'plus.stream.upstream.bytes_sent', 'plus.stream.upstream.bytes_rcvd',
            'plus.stream.upstream.fails.count', 'plus.stream.upstream.unavail.count',
            'plus.stream.upstream.health.checks', 'plus.stream.upstream.health.fails',
            'plus.stream.upstream.health.unhealthy',
        ):
            assert_that(counters, has_key(key))

        assert_that(counters['plus.stream.upstream.conn.count'][0], equal_to([2, 100]))

    def test_collect_complete(self):
        stream_upstream = NginxApiStreamUpstreamObject(
            local_name='backend',
            parent_local_id='nginx123',
            root_uuid='root123'
        )
        stream_upstream.api_internal_url_cache = 'test_api'

        # Get the stream_upstream collector
        stream_upstream_collector = stream_upstream.collectors[-1]
        assert_that(stream_upstream_collector.last_collect, equal_to(None))

        context.plus_cache.put('test_api', (
            {
                u'stream': {
                    u'upstreams' : {
                        u'backend': {
                            u'peers': [
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 0,
                                    u'name': u'backend1.example.com:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'198.105.254.130:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 5,
                                    u'first_byte_time': 223,
                                    u'connect_time': 22,
                                    u'response_time': 11,
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 1,
                                    u'name': u'backend1.example.com:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'104.239.207.44:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 5
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 2,
                                    u'name': u'127.0.0.1:12345',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'127.0.0.1:12345',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 1
                                },
                                {
                                    u'active': 0,
                                    u'backup': False,
                                    u'connections': 0,
                                    u'downstart': 0,
                                    u'downtime': 0,
                                    u'fails': 0,
                                    u'health_checks': {
                                        u'checks': 0,
                                        u'fails': 0,
                                        u'unhealthy': 0
                                    },
                                    u'id': 3,
                                    u'name': u'unix:/tmp/backend3',
                                    u'received': 0,
                                    u'selected': 0,
                                    u'sent': 0,
                                    u'server': u'unix:/tmp/backend3',
                                    u'state': u'up',
                                    u'unavail': 0,
                                    u'weight': 1
                                }
                            ],
                            u'zombies': 0,
                            u'zone': u'up-backend'
                        }
                    }
                }
            },
            1
        ))

        stream_upstream_collector.collect()
        assert_that(stream_upstream_collector.last_collect, equal_to(1))

        assert_that(stream_upstream.statsd.current, not_(has_length(0)))
        assert_that(stream_upstream.statsd.current, not_(has_key('counter')))
        assert_that(stream_upstream.statsd.current, has_key('timer'))
        timers = stream_upstream.statsd.current['timer']

        for key in (
            'plus.stream.upstream.conn.ttfb', 'plus.stream.upstream.conn.time',
            'plus.stream.upstream.response.time'
        ):
            assert_that(timers, has_key(key))

        assert_that(timers['plus.stream.upstream.conn.ttfb'][0], equal_to(0.223))
