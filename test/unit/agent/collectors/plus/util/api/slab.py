# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.context import context
from amplify.agent.objects.plus.api import NginxApiSlabObject

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class SlabCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(SlabCollectorTestCase, self).setup_method(method)
        context.plus_cache = None
        context._setup_plus_cache()

    def test_gather_data(self):
        slab_obj = NginxApiSlabObject(local_name=u'h1u', parent_local_id='nginx123', root_uuid='root123')
        # Do a quick override of api_internal_url_cache
        slab_obj.api_internal_url_cache = 'test_api'

        # Get the slab collector
        slab_collector = slab_obj.collectors[-1]

        # Insert some dummy data
        context.plus_cache.put('test_api', (
            {
                u'slabs': {
                    u'h1u': {
                        u'pages': {u'free': 2, u'used': 5},
                        u'slots': {
                            u'1024': {u'fails': 0, u'free': 0, u'reqs': 0,u'used': 0},
                            u'128': {u'fails': 0, u'free': 26, u'reqs': 6, u'used': 6},
                            u'16': {u'fails': 0, u'free': 251, u'reqs': 3, u'used': 3},
                            u'2048': {u'fails': 0,  u'free': 0, u'reqs': 0, u'used': 0},
                            u'256': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'32': {u'fails': 0, u'free': 124, u'reqs': 3,  u'used': 3},
                            u'512': {u'fails': 0, u'free': 6, u'reqs': 2, u'used': 2},
                            u'64': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'8': {u'fails': 0, u'free': 502, u'reqs': 2, u'used': 2}
                        }
                    }
                },
            },
            1
        ))

        data = slab_collector.gather_data()

        assert_that(data, not_(equal_to([])))
        assert_that(data, has_length(1))

    def test_collect(self):
        slab_obj = NginxApiSlabObject(local_name=u'h1u', parent_local_id='nginx123', root_uuid='root123')
        # Do a quick override of api_internal_url_cache
        slab_obj.api_internal_url_cache = 'test_api'

        # Get the slab collector
        slab_collector = slab_obj.collectors[-1]
        assert_that(slab_collector.last_collect, equal_to(None))

        # Insert some dummy data
        context.plus_cache.put('test_api', (
            {
                u'slabs': {
                    u'h1u': {
                        u'pages': {u'free': 2, u'used': 4},
                        u'slots': {
                            u'1024': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'128': {u'fails': 0, u'free': 26, u'reqs': 6, u'used': 6},
                            u'16': {u'fails': 0, u'free': 251, u'reqs': 3, u'used': 3},
                            u'2048': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'256': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'32': {u'fails': 0, u'free': 124, u'reqs': 3, u'used': 3},
                            u'512': {u'fails': 0, u'free': 6, u'reqs': 2, u'used': 2},
                            u'64': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'8': {u'fails': 0, u'free': 502, u'reqs': 2, u'used': 2}
                        }
                    }
                },
            },
            1
        ))

        context.plus_cache.put('test_api', (
            {
                u'slabs': {
                    u'h1u': {
                        u'pages': {u'free': 5, u'used': 30},
                        u'slots': {
                            u'1024': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'128': {u'fails': 0, u'free': 26, u'reqs': 6, u'used': 6},
                            u'16': {u'fails': 0, u'free': 251, u'reqs': 3, u'used': 3},
                            u'2048': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'256': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'32': {u'fails': 0, u'free': 124, u'reqs': 3, u'used': 3},
                            u'512': {u'fails': 0, u'free': 6, u'reqs': 2, u'used': 2},
                            u'64': {u'fails': 0, u'free': 0, u'reqs': 0, u'used': 0},
                            u'8': {u'fails': 0, u'free': 502, u'reqs': 2, u'used': 2}
                        }
                    }
                },
            },
            2
        ))

        slab_collector.collect()
        assert_that(slab_collector.last_collect, equal_to(2))

        assert_that(slab_obj.statsd.current, not_(has_length(0)))

        assert_that(slab_obj.statsd.current, has_key('gauge'))
        gauges = slab_obj.statsd.current['gauge']
        print gauges

        for key in (
            'plus.slab.pages.free',
            'plus.slab.pages.used',
            'plus.slab.pages.total',
            'plus.slab.pages.pct_used'
        ):
            assert_that(gauges, has_key(key))

        assert_that(gauges['plus.slab.pages.pct_used'][0], equal_to((1, 33)))
        assert_that(gauges['plus.slab.pages.total'][0], equal_to((1, 6)))
