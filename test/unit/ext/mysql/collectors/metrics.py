# -*- coding: utf-8 -*-
import time
import pymysql

from hamcrest import *

from test.unit.ext.mysql.base import MySQLTestCase
from amplify.agent.common.context import context
from amplify.ext.mysql.objects import MySQLObject
from amplify.ext.mysql.collectors.metrics import MySQLMetricsCollector, METRICS

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class MySQLMetricsCollectorTestCase(MySQLTestCase):

    def setup_method(self, method):
        super(MySQLMetricsCollectorTestCase, self).setup_method(method)
        context._setup_object_tank()

        self.mysql_obj = MySQLObject(
            local_id=123,
            pid=2,
            cmd='/usr/sbin/mysqld --basedir=/usr',
            conf_path='/etc/mysql/my.cnf',
        )

        context.objects.register(self.mysql_obj)

    def teardown_method(self, method):
        context._setup_object_tank()
        super(MySQLMetricsCollectorTestCase, self).setup_method(method)

    def make_selects(self, amount=5):
        c = pymysql.connect(**self.mysql_obj.connection_args)
        cursor = c.cursor()
        for i in xrange(amount):
            cursor.execute("SELECT 1 FROM DUAL;")
            cursor.fetchone()
        c.close()

    def test_init(self):
        mysql_metrics_collector = MySQLMetricsCollector(
            object=self.mysql_obj,
            interval=self.mysql_obj.intervals['metrics']
        )
        assert_that(mysql_metrics_collector, not_none())
        assert_that(mysql_metrics_collector, is_(MySQLMetricsCollector))

    def test_collect(self):
        mysql_metrics_collector = MySQLMetricsCollector(
            object=self.mysql_obj,
            interval=self.mysql_obj.intervals['metrics']
        )

        # collect first time
        mysql_metrics_collector.collect()

        # sleep and do some selects
        time.sleep(1)
        self.make_selects()

        # collect second time
        mysql_metrics_collector.collect()

        # check counters
        counters = self.mysql_obj.statsd.current['counter']
        for metric_name in METRICS['counters'].iterkeys():
            assert_that(counters, has_key(metric_name))
        assert_that(counters['mysql.global.select'][0][1], equal_to(5))

        # check gauges
        gauges = self.mysql_obj.statsd.current['gauge']
        for metric_name in METRICS['gauges'].iterkeys():
            assert_that(gauges, has_key(metric_name))
