# -*- coding: utf-8 -*-
from amplify.agent.common.util.plus import traverse_plus_api, get_latest_supported_api
from amplify.agent.common.util import plus
from hamcrest import *
from test.base import RealNginxTestCase, nginx_plus_test
import time

__author__ = "Raymond Lau"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Raymond Lau"
__email__ = "raymond.lau@nginx.com"


class PlusTestCase(RealNginxTestCase):

    def setup_method(self, method):
        super(PlusTestCase, self).setup_method(method)
        self.original_supported_versions = plus.SUPPORTED_API_VERSIONS

    def teardown_method(self, method):
        plus.SUPPORTED_API_VERSIONS = self.original_supported_versions
        super(PlusTestCase, self).teardown_method(method)

    @nginx_plus_test
    def test_get_latest_supported_api(self):
        time.sleep(1)  # Give N+ some time to start

        current_api = get_latest_supported_api("https://127.0.0.1:443/api")
        # equal_to will need to be updated once later versions are released
        assert_that(current_api, equal_to("https://127.0.0.1:443/api/2"))

        plus.SUPPORTED_API_VERSIONS = [1]
        current_api = get_latest_supported_api("https://127.0.0.1:443/api")
        assert_that(current_api, equal_to("https://127.0.0.1:443/api/1"))

    @nginx_plus_test
    def test_get_latest_supported_api_none(self):
        time.sleep(1)  # Give N+ some time to start
        
        plus.SUPPORTED_API_VERSIONS = [0]
        current_api = get_latest_supported_api("https://127.0.0.1:443/api")
        assert_that(current_api, equal_to(None))

    @nginx_plus_test
    def test_traverse_plus_api(self):
        time.sleep(1)  # Give N+ some time to start

        combined_api_payload = traverse_plus_api("https://127.0.0.1:443/api")

        assert_that(combined_api_payload, has_key('nginx'))
        assert_that(combined_api_payload, has_key('processes'))
        assert_that(combined_api_payload, has_key('connections'))
        assert_that(combined_api_payload, has_key('ssl'))
        assert_that(combined_api_payload, has_key('slabs'))
        assert_that(combined_api_payload, has_key('http'))
        assert_that(combined_api_payload, has_key('stream'))

        # check that function traverses recursively
        assert_that(combined_api_payload['http'], has_key('requests'))
        assert_that(combined_api_payload['http'], has_key('caches'))
        assert_that(combined_api_payload['http'], has_key('server_zones'))
        assert_that(combined_api_payload['http'], has_key('upstreams'))
        assert_that(combined_api_payload['http'], has_key('keyvals'))
        assert_that(combined_api_payload['stream'], has_key('upstreams'))
        assert_that(combined_api_payload['stream'], has_key('server_zones'))
        assert_that(combined_api_payload['stream'], has_key('keyvals'))

    @nginx_plus_test
    def test_traverse_plus_api_with_skip(self):
        # this test assumes that test-plus nginx.conf initially has a stream directive defined
        time.sleep(1)

        combined_api_payload = traverse_plus_api("https://127.0.0.1:443/api", root_endpoints_to_skip=['stream'])

        assert_that(combined_api_payload, has_key('http'))
        assert_that(combined_api_payload, has_key('stream'))

        assert_that(combined_api_payload['http'], not_(equal_to({})))
        assert_that(combined_api_payload['stream'], equal_to({}))