# -*- coding: utf-8 -*-
from copy import deepcopy

from hamcrest import *

from amplify.agent.common.context import context
from amplify.agent.managers.nginx import NginxManager
from amplify.agent.objects.nginx.config.config import NginxConfig
from test.base import RealNginxTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class ConfigCollectorTestCase(RealNginxTestCase):

    def setup_method(self, method):
        super(ConfigCollectorTestCase, self).setup_method(method)
        self.max_test_time = deepcopy(context.app_config['containers']['nginx']['max_test_duration'])
        self.original_full_parse = NginxConfig.full_parse

    def teardown_method(self, method):
        context.app_config['containers']['nginx']['max_test_duration'] = deepcopy(self.max_test_time)
        NginxConfig.full_parse = self.original_full_parse
        super(ConfigCollectorTestCase, self).teardown_method(method)

    def test_collect(self):
        manager = NginxManager()
        manager._discover_objects()

        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]
        cfg_collector = nginx_obj.collectors[0]

        # run collect
        cfg_collector.collect()
        assert_that(nginx_obj.configd.current, not_(empty()))

    def test_skip_parse_until_change(self):
        manager = NginxManager()

        # wrap NginxConfig.full_parse with a method that counts how many times it's been called
        def count_full_parse_calls(config_obj, include_ssl_certs):
            NginxConfig.__full_parse_calls += 1
            config_obj.__full_parse()

        NginxConfig.__full_parse_calls = 0
        NginxConfig.__full_parse = NginxConfig.full_parse
        NginxConfig.full_parse = count_full_parse_calls

        # discover the NGINX object and check that the config has been fully parsed once
        manager._discover_objects()
        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]
        assert_that(NginxConfig.__full_parse_calls, equal_to(1))

        # get the NginxConfig collector
        cfg_collector = nginx_obj.collectors[0]

        # check that NginxConfig.full_parse is not called again during collect
        cfg_collector.collect(no_delay=True)
        assert_that(NginxConfig.__full_parse_calls, equal_to(1))
        cfg_collector.collect(no_delay=True)
        cfg_collector.collect(no_delay=True)
        assert_that(NginxConfig.__full_parse_calls, equal_to(1))

        # change the collector's previous files record so that it will call full_parse
        cfg_collector.previous['files'] = {}
        cfg_collector.collect(no_delay=True)
        assert_that(NginxConfig.__full_parse_calls, equal_to(2))
        cfg_collector.collect(no_delay=True)
        cfg_collector.collect(no_delay=True)
        assert_that(NginxConfig.__full_parse_calls, equal_to(2))

        # change the collector's previous directories record and check that it does not call full_parse
        cfg_collector.previous['directories'] = {}
        cfg_collector.collect(no_delay=True)
        assert_that(NginxConfig.__full_parse_calls, equal_to(2))
        cfg_collector.collect(no_delay=True)
        cfg_collector.collect(no_delay=True)
        assert_that(NginxConfig.__full_parse_calls, equal_to(2))

    def test_test_run_time(self):
        manager = NginxManager()
        manager._discover_objects()

        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]
        cfg_collector = nginx_obj.collectors[0]
        assert_that(nginx_obj.run_config_test, equal_to(True))

        # set maximum run time for test to 0.0
        context.app_config['containers']['nginx']['max_test_duration'] = 0.0

        # running collect won't do anything until the config changes
        cfg_collector.collect(no_delay=True)
        assert_that(nginx_obj.run_config_test, equal_to(True))

        # change the collector's previous files record so that it will call full_parse
        cfg_collector.previous['files'] = {}

        # running collect should now cause the run_time to exceed 0.0, rendering run_config_test False
        cfg_collector.collect(no_delay=True)
        assert_that(nginx_obj.run_config_test, equal_to(False))

        events = nginx_obj.eventd.current.values()
        messages = []
        for event in events:
            messages.append(event.message)

        assert_that(messages, has_item(starts_with('/usr/sbin/nginx -t -c /etc/nginx/nginx.conf took')))


class ConfigCollectorSSLTestCase(RealNginxTestCase):

    def setup_method(self, method):
        super(ConfigCollectorSSLTestCase, self).setup_method(method)
        self.original_upload_ssl = deepcopy(context.app_config['containers']['nginx']['upload_ssl'])

    def teardown_method(self, method):
        context.app_config['containers']['nginx']['upload_ssl'] = deepcopy(self.original_upload_ssl)
        super(ConfigCollectorSSLTestCase, self).teardown_method(method)

    def test_ssl_config_works_if_ssl_enabled(self):
        # set upload_ssl to True
        context.app_config['containers']['nginx']['upload_ssl'] = True

        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.objects_by_type[manager.type], has_length(1))

        # get nginx object
        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]
        cfg_collector = nginx_obj.collectors[0]
        cfg_collector.collect()

        config = nginx_obj.configd.current
        assert_that(config['data']['ssl_certificates'], has_length(1))

    def test_ssl_config_doesnt_work_if_ssl_disabled(self):
        # set upload_ssl to True
        context.app_config['containers']['nginx']['upload_ssl'] = False

        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.objects_by_type[manager.type], has_length(1))

        # get nginx object
        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]
        cfg_collector = nginx_obj.collectors[0]
        cfg_collector.collect()

        config = nginx_obj.configd.current
        assert_that(config['data']['ssl_certificates'], has_length(0))
