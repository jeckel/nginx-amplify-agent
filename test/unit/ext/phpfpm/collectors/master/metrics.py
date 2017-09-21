# -*- coding: utf-8 -*-
from hamcrest import (
    assert_that, not_none, is_, equal_to, has_item, has_length, not_
)
import time

from test.unit.ext.phpfpm.base import PHPFPMTestCase

from amplify.agent.common.context import context

from amplify.ext.phpfpm.objects.master import PHPFPMObject
from amplify.ext.phpfpm.collectors.master.metrics import PHPFPMMetricsCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMMetricsCollectorTestCase(PHPFPMTestCase):
    """
    Test case for PHPFPMMetricsCollector
    """

    def setup_method(self, method):
        super(PHPFPMMetricsCollectorTestCase, self).setup_method(method)
        context._setup_object_tank()

        self.phpfpm_obj = PHPFPMObject(
            local_id=123,
            pid=2,
            cmd='php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
            conf_path='/etc/php5/fpm/php-fpm.conf',
            workers=[3, 4]
        )

        context.objects.register(self.phpfpm_obj)

    def teardown_method(self, method):
        context._setup_object_tank()
        super(PHPFPMMetricsCollectorTestCase, self).setup_method(method)

    def test_init(self):
        phpfpm_metrics_collector = PHPFPMMetricsCollector(
            object=self.phpfpm_obj,
            interval=self.phpfpm_obj.intervals['metrics']
        )
        assert_that(phpfpm_metrics_collector, not_none())
        assert_that(phpfpm_metrics_collector, is_(PHPFPMMetricsCollector))

    def test_collect(self):
        phpfpm_metrics_collector = PHPFPMMetricsCollector(
            object=self.phpfpm_obj,
            interval=self.phpfpm_obj.intervals['metrics']
        )
        assert_that(phpfpm_metrics_collector, not_none())

        counted_vars = {
            'php.fpm.queue.req': 0,
            'php.fpm.slow_req': 0,
            'php.fpm.conn.accepted': 3
        }
        counted_vars_2 = {
            'php.fpm.queue.req': 5,
            'php.fpm.slow_req': 4,
            'php.fpm.conn.accepted': 5
        }

        # make direct aggregate call like a child collector would
        phpfpm_metrics_collector.aggregate_counters(
            counted_vars=counted_vars, stamp=1
        )

        # collect (runs increment)
        phpfpm_metrics_collector.collect()
        time.sleep(0.1)

        # first collect should not have counters
        assert_that(self.phpfpm_obj.statsd.current, not_(has_item('counter')))

        # make a second call
        phpfpm_metrics_collector.aggregate_counters(
            counted_vars=counted_vars_2, stamp=2
        )

        phpfpm_metrics_collector.collect()
        time.sleep(0.1)

        # now there should be counters
        assert_that(self.phpfpm_obj.statsd.current, has_item('counter'))

        counters = self.phpfpm_obj.statsd.current['counter']
        assert_that(counters, has_length(3))
        """
        counters:
        {
            'php.fpm.queue.req': [[2, 5]],
            'php.fpm.slow_req': [[2, 4]],
            'php.fpm.conn.accepted': [[2, 2]]
        }
        """
        assert_that(counters['php.fpm.queue.req'][0][1], equal_to(5))
        assert_that(counters['php.fpm.slow_req'][0][1], equal_to(4))
        assert_that(counters['php.fpm.conn.accepted'][0][1], equal_to(2))

        for metric_records in counters.itervalues():
            # get stamp from first recording in records
            stamp = metric_records[0][0]
            assert_that(stamp, equal_to(2))

    def test_gauge_aggregation(self):
        phpfpm_metrics_collector = PHPFPMMetricsCollector(
            object=self.phpfpm_obj,
            interval=self.phpfpm_obj.intervals['metrics']
        )
        assert_that(phpfpm_metrics_collector, not_none())

        tracked_gauges_source1 = {
            'php.fpm.proc.idle': {'source1': 1},
            'php.fpm.proc.active': {'source1': 1},
            'php.fpm.proc.total': {'source1': 2}
        }
        tracked_gauges_source2 = {
            'php.fpm.proc.idle': {'source2': 1},
            'php.fpm.proc.active': {'source2': 1},
            'php.fpm.proc.total': {'source2': 2}
        }

        # make direct aggregate call like a child would
        phpfpm_metrics_collector.aggregate_gauges(
            tracked_gauges_source1, stamp=1
        )
        phpfpm_metrics_collector.aggregate_gauges(
            tracked_gauges_source2, stamp=2
        )

        # collect (runs finalize)
        phpfpm_metrics_collector.collect()
        time.sleep(0.1)

        assert_that(self.phpfpm_obj.statsd.current, has_item('gauge'))

        gauges = self.phpfpm_obj.statsd.current['gauge']
        assert_that(gauges, has_length(3))
        """
        gauges:
        {
            'php.fpm.proc.idle': [[2, 2]],
            'php.fpm.proc.active': [[2, 2]],
            'php.fpm.proc.total': [[2, 4]]
        }
        """
        assert_that(gauges['php.fpm.proc.idle'][0][1], equal_to(2))
        assert_that(gauges['php.fpm.proc.active'][0][1], equal_to(2))
        assert_that(gauges['php.fpm.proc.total'][0][1], equal_to(4))

        for metric_record in gauges.itervalues():
            stamp = metric_record[0][0]
            assert_that(stamp, equal_to(2))
