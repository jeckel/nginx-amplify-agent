# -*- coding: utf-8 -*-
import time

from hamcrest import *

from amplify.agent.common.util import plus
from amplify.agent.managers.nginx import NginxManager
from test.base import RealNginxTestCase, nginx_plus_test

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class NginxMetricsTestCase(RealNginxTestCase):

    def setup_method(self, method):
        super(NginxMetricsTestCase, self).setup_method(method)
        self.original_supported_versions = plus.SUPPORTED_API_VERSIONS

    def teardown_method(self, method):
        plus.SUPPORTED_API_VERSIONS = self.original_supported_versions
        super(NginxMetricsTestCase, self).teardown_method(method)

    def test_stub_status(self):
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        # get nginx object
        nginx_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run plus status - twice, because counters will appear only on the second run
        metrics_collector.stub_status()
        time.sleep(1)
        metrics_collector.stub_status()

        # check counters
        metrics = nginx_obj.statsd.current
        assert_that(metrics, has_item('counter'))
        counters = metrics['counter']
        assert_that(counters, has_item('nginx.http.conn.accepted'))
        assert_that(counters, has_item('nginx.http.request.count'))
        assert_that(counters, has_item('nginx.http.conn.dropped'))

        # check gauges
        assert_that(metrics, has_item('gauge'))
        gauges = metrics['gauge']
        assert_that(gauges, has_item('nginx.http.conn.active'))
        assert_that(gauges, has_item('nginx.http.conn.current'))
        assert_that(gauges, has_item('nginx.http.conn.idle'))
        assert_that(gauges, has_item('nginx.http.request.current'))
        assert_that(gauges, has_item('nginx.http.request.writing'))
        assert_that(gauges, has_item('nginx.http.request.reading'))

    @nginx_plus_test
    def test_plus_status(self):
        time.sleep(1)  # Give N+ some time to start
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        # get nginx object
        nginx_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run plus status - twice, because counters will appear only on the second run
        metrics_collector.plus_status()
        time.sleep(1)
        metrics_collector.plus_status()

        # check counters
        metrics = nginx_obj.statsd.current
        assert_that(metrics, has_item('counter'))
        counters = metrics['counter']
        assert_that(counters, has_item('nginx.http.conn.accepted'))
        assert_that(counters, has_item('nginx.http.request.count'))
        assert_that(counters, has_item('nginx.http.conn.dropped'))
        assert_that(counters, has_item('plus.http.ssl.handshakes'))
        assert_that(counters, has_item('plus.http.ssl.failed'))
        assert_that(counters, has_item('plus.http.ssl.reuses'))

        # check gauges
        assert_that(metrics, has_item('gauge'))
        gauges = metrics['gauge']
        assert_that(gauges, has_item('nginx.http.conn.active'))
        assert_that(gauges, has_item('nginx.http.conn.current'))
        assert_that(gauges, has_item('nginx.http.conn.idle'))
        assert_that(gauges, has_item('nginx.http.request.current'))

    @nginx_plus_test
    def test_plus_api(self):
        time.sleep(1)
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        # get nginx object
        nginx_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run plus api - twice, because counters will appear only on the second run
        metrics_collector.plus_api()
        time.sleep(1)
        metrics_collector.plus_api()

        # check counters
        metrics = nginx_obj.statsd.current
        assert_that(metrics, has_item('counter'))
        counters = metrics['counter']
        assert_that(counters, has_item('nginx.http.conn.accepted'))
        assert_that(counters, has_item('nginx.http.request.count'))
        assert_that(counters, has_item('nginx.http.conn.dropped'))
        assert_that(counters, has_item('plus.http.ssl.handshakes'))
        assert_that(counters, has_item('plus.http.ssl.failed'))
        assert_that(counters, has_item('plus.http.ssl.reuses'))
        assert_that(counters, has_item('plus.proc.respawned'))

        # check gauges
        assert_that(metrics, has_item('gauge'))
        gauges = metrics['gauge']
        assert_that(gauges, has_item('nginx.http.conn.active'))
        assert_that(gauges, has_item('nginx.http.conn.current'))
        assert_that(gauges, has_item('nginx.http.conn.idle'))
        assert_that(gauges, has_item('nginx.http.request.current'))

    @nginx_plus_test
    def test_plus_api_unsupported_and_fallback_to_status(self):
        """
        Checks that api_enabled is set to False if no supported API version is found
        """
        plus.SUPPORTED_API_VERSIONS = [0]

        time.sleep(1)
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        nginx_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]

        # api_enabled should be set to false in metrics collector __init__
        assert_that(nginx_obj.api_enabled, equal_to(False))
        assert_that(nginx_obj.plus_status_enabled, equal_to(True))

        metrics_collector = nginx_obj.collectors[2]

        # run plus status - twice, because counters will appear only on the second run
        metrics_collector.global_metrics()
        time.sleep(1)
        metrics_collector.global_metrics()

        # check counters
        metrics = nginx_obj.statsd.current
        assert_that(metrics, has_item('counter'))
        counters = metrics['counter']
        assert_that(counters, has_item('nginx.http.conn.accepted'))
        assert_that(counters, has_item('nginx.http.request.count'))
        assert_that(counters, has_item('nginx.http.conn.dropped'))
        assert_that(counters, has_item('plus.http.ssl.handshakes'))
        assert_that(counters, has_item('plus.http.ssl.failed'))
        assert_that(counters, has_item('plus.http.ssl.reuses'))
        # to check it actually fell back to old plus status
        assert_that(counters, not_(has_item('plus.proc.respawned')))

        # check gauges
        assert_that(metrics, has_item('gauge'))
        gauges = metrics['gauge']
        assert_that(gauges, has_item('nginx.http.conn.active'))
        assert_that(gauges, has_item('nginx.http.conn.current'))
        assert_that(gauges, has_item('nginx.http.conn.idle'))
        assert_that(gauges, has_item('nginx.http.request.current'))

    @nginx_plus_test
    def test_global_metrics_priority_api_disabled(self):
        """
        Checks that if we can reach plus status then we don't use stub_status
        """
        time.sleep(1)  # Give N+ some time to start
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        # get nginx object
        nginx_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]
        nginx_obj.api_enabled = False

        # check that it has n+ status and stub_status enabled
        assert_that(nginx_obj.plus_status_enabled, equal_to(True))
        assert_that(nginx_obj.stub_status_enabled, equal_to(True))

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run status twice
        metrics_collector.global_metrics()
        time.sleep(1)
        metrics_collector.global_metrics()

        # check gauges - we should't see request.writing/reading here, because n+ status doesn't have those
        metrics = nginx_obj.statsd.current
        assert_that(metrics, has_item('gauge'))
        gauges = metrics['gauge']
        assert_that(gauges, not_(has_item('nginx.http.request.writing')))
        assert_that(gauges, not_(has_item('nginx.http.request.reading')))

        # plus status should not have this.  it's new in plus api
        assert_that(metrics, has_item('counter'))
        counters = metrics['counter']
        assert_that(counters, not_(has_item('plus.proc.respawned')))
        assert_that(counters, has_item('nginx.http.conn.accepted'))
        assert_that(counters, has_item('nginx.http.request.count'))
        assert_that(counters, has_item('nginx.http.conn.dropped'))
        assert_that(counters, has_item('plus.http.ssl.handshakes'))
        assert_that(counters, has_item('plus.http.ssl.failed'))
        assert_that(counters, has_item('plus.http.ssl.reuses'))

        # check gauges
        assert_that(gauges, has_item('nginx.http.conn.active'))
        assert_that(gauges, has_item('nginx.http.conn.current'))
        assert_that(gauges, has_item('nginx.http.conn.idle'))
        assert_that(gauges, has_item('nginx.http.request.current'))


    @nginx_plus_test
    def test_global_metrics_priority_api_enabled(self):
        """
        Checks that if we can reach plus status then we don't use stub_status
        """
        time.sleep(1)  # Give N+ some time to start
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        # get nginx object
        nginx_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]

        # check that it has n+ api, n+ status, stub_status enabled
        assert_that(nginx_obj.api_enabled, equal_to(True))
        assert_that(nginx_obj.plus_status_enabled, equal_to(True))
        assert_that(nginx_obj.stub_status_enabled, equal_to(True))

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run status twice
        metrics_collector.global_metrics()
        time.sleep(1)
        metrics_collector.global_metrics()

        metrics = nginx_obj.statsd.current

        # this stat is new in n+ api, but is not in status nor stub_status
        assert_that(metrics, has_item('counter'))
        counters = metrics['counter']
        assert_that(counters, has_item('plus.proc.respawned'))


    @nginx_plus_test
    def test_plus_ssl_metrics(self):
        """
        Checks that we collect ssl metrics
        """
        time.sleep(1)  # Give N+ some time to start
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        # get nginx object
        nginx_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run status twice
        metrics_collector.global_metrics()
        time.sleep(1)
        metrics_collector.global_metrics()

        # check ssl counters
        metrics = nginx_obj.statsd.current
        assert_that(metrics, has_item('counter'))
        counters = metrics['counter']
        assert_that(counters, has_item('plus.http.ssl.handshakes'))
        assert_that(counters, has_item('plus.http.ssl.failed'))
        assert_that(counters, has_item('plus.http.ssl.reuses'))
