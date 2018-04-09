# -*- coding: utf-8 -*-
import time
from hamcrest import *

from test.base import RealNginxTestCase, nginx_plus_test

from amplify.agent.common.context import context
from amplify.agent.managers.nginx import NginxManager
from amplify.agent.managers.status import StatusManager
from amplify.agent.managers.api import ApiManager


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class StatusManagerTestCase(RealNginxTestCase):
    plus_manager = StatusManager
    api = False
    collector_method = 'plus_status'

    def setup_method(self, method):
        super(StatusManagerTestCase, self).setup_method(method)
        context.objects = None
        context._setup_object_tank()

    def teardown_method(self, method):
        context.objects = None
        context._setup_object_tank()
        super(StatusManagerTestCase, self).teardown_method(method)

    @nginx_plus_test
    def test_discover(self):
        nginx_manager = NginxManager()
        nginx_manager._discover_objects()
        assert_that(nginx_manager.objects.objects_by_type[nginx_manager.type], has_length(1))

        # get nginx object
        nginx_obj = nginx_manager.objects.objects[nginx_manager.objects.objects_by_type[nginx_manager.type][0]]
        # dont want manager to skip this nginx object
        nginx_obj.api_enabled = self.api

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run plus status - twice, because counters will appear only on the second run
        getattr(metrics_collector, self.collector_method)()
        time.sleep(1)
        getattr(metrics_collector, self.collector_method)()

        plus_manager = self.plus_manager()
        plus_manager._discover_objects()
        assert_that(plus_manager.objects.find_all(types=plus_manager.types), has_length(10))

    @nginx_plus_test
    def test_discover_ignore_api_objects(self):
        if self.plus_manager.__name__ != 'StatusManager':
            # this test only applies to old status manager
            return

        nginx_manager = NginxManager()
        nginx_manager._discover_objects()
        assert_that(nginx_manager.objects.objects_by_type[nginx_manager.type], has_length(1))

        # get nginx object
        nginx_obj = nginx_manager.objects.objects[nginx_manager.objects.objects_by_type[nginx_manager.type][0]]

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run plus status/api - twice, because counters will appear only on the second run
        getattr(metrics_collector, self.collector_method)()
        metrics_collector.plus_api()
        time.sleep(1)
        getattr(metrics_collector, self.collector_method)()
        metrics_collector.plus_api()

        plus_manager = self.plus_manager()

        # since objects are stored in the same object tank,
        # make sure there is no overlap
        api_manager = ApiManager()
        api_manager._discover_objects()
        assert_that(api_manager._api_objects(), has_length(10))
        assert_that(plus_manager._status_objects(), has_length(0))

        nginx_obj.api_enabled = self.api
        plus_manager._discover_objects()
        api_manager._discover_objects()
        assert_that(api_manager._api_objects(), has_length(0))
        assert_that(plus_manager._status_objects(), has_length(10))

    @nginx_plus_test
    def test_rejuvenation(self):
        nginx_manager = NginxManager()
        nginx_manager._discover_objects()
        assert_that(nginx_manager.objects.objects_by_type[nginx_manager.type], has_length(1))

        # get nginx object
        nginx_obj = nginx_manager.objects.objects[nginx_manager.objects.objects_by_type[nginx_manager.type][0]]
        # dont want manager to skip this nginx object
        nginx_obj.api_enabled = self.api

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run plus status - twice, because counters will appear only on the second run
        getattr(metrics_collector, self.collector_method)()
        time.sleep(1)
        getattr(metrics_collector, self.collector_method)()

        plus_manager = self.plus_manager()
        plus_manager._discover_objects()
        assert_that(plus_manager.objects.find_all(types=plus_manager.types), has_length(10))

        self.stop_first_nginx()

        nginx_manager = NginxManager()
        nginx_manager._discover_objects()
        assert_that(nginx_manager.objects.objects_by_type[nginx_manager.type], has_length(0))

        plus_manager = self.plus_manager()
        plus_manager._discover_objects()
        assert_that(plus_manager.objects.find_all(types=plus_manager.types), has_length(0))

        self.start_first_nginx()

        nginx_manager = NginxManager()
        nginx_manager._discover_objects()
        assert_that(nginx_manager.objects.objects_by_type[nginx_manager.type], has_length(1))

        # get nginx object
        nginx_obj = nginx_manager.objects.objects[nginx_manager.objects.objects_by_type[nginx_manager.type][0]]
        # dont want manager to skip this nginx object
        nginx_obj.api_enabled = self.api

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run plus status - twice, because counters will appear only on the second run
        getattr(metrics_collector, self.collector_method)()
        time.sleep(1)
        getattr(metrics_collector, self.collector_method)()

        plus_manager = self.plus_manager()
        plus_manager._discover_objects()
        assert_that(plus_manager.objects.find_all(types=plus_manager.types), has_length(10))
