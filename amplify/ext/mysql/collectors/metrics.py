# -*- coding: utf-8 -*-
import pymysql
import time

from amplify.agent.common.context import context
from amplify.agent.collectors.abstract import AbstractMetricsCollector

__author__ = "Andrew Alexeev"
__copyright__ = "Copyright (C) Nginx Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


METRICS = {
    'counters': {
        'mysql.global.connections': 'Connections',
        'mysql.global.questions': 'Questions',
        'mysql.global.select': 'Com_select',
        'mysql.global.insert': 'Com_insert',
        'mysql.global.update': 'Com_update',
        'mysql.global.delete': 'Com_delete',
        'mysql.global.commit': 'Com_commit',
        'mysql.global.slow_queries': 'Slow_queries',
        'mysql.global.uptime': 'Uptime',
        'mysql.global.aborted_connects': 'Aborted_connects',
        'mysql.global.innodb_buffer_pool_read_requests': 'Innodb_buffer_pool_read_requests',
        'mysql.global.innodb_buffer_pool_reads': 'Innodb_buffer_pool_reads'
    },
    'gauges': {
        'mysql.global.threads_connected': 'Threads_connected',
        'mysql.global.threads_running': 'Threads_running'
    }
}

REQUIRED_STATUS_FIELDS = METRICS['counters'].values() + METRICS['gauges'].values()


class MySQLMetricsCollector(AbstractMetricsCollector):
    """
    Metrics collector.  Spawned per master.
    """
    short_name = 'mysql_metrics'

    def __init__(self, **kwargs):
        super(MySQLMetricsCollector, self).__init__(**kwargs)

        self.register(
            self.mysql_status
        )

    def mysql_status(self):
        """
        Collects data from MySQLd instance

        :param args: *args
        :param kwargs: **kwargs
        """
        stamp = int(time.time())

        # open a connection
        try:
            c = pymysql.connect(**self.object.connection_args)  # these are coming from agent config for now
        except Exception as e:
            exception_name = e.__class__.__name__
            context.log.debug('failed to connect to MySQLd due to %s' % exception_name)
            context.log.debug('additional info:', exc_info=True)
            raise

        # get data
        result = {}
        try:
            cursor = c.cursor()
            for key in REQUIRED_STATUS_FIELDS:
                cursor.execute('SHOW GLOBAL STATUS LIKE "%s";' % key)
                row = cursor.fetchone()
                result[row[0]] = row[1]
        except Exception as e:
            exception_name = e.__class__.__name__
            context.log.debug('failed to collect MySQLd metrics due to %s' % exception_name)
            context.log.debug('additional info:', exc_info=True)

        # close the connection
        c.close()

        # counters
        counted_vars = {}
        for metric, variable_name in METRICS['counters'].iteritems():
            if variable_name in result:
                counted_vars[metric] = int(result[variable_name])
        self.aggregate_counters(counted_vars, stamp=stamp)

        # gauges
        tracked_gauges = {}
        for metric, variable_name in METRICS['gauges'].iteritems():
            if variable_name in result:
                tracked_gauges[metric] = {
                    self.object.definition_hash: int(result[variable_name])
                }
        self.aggregate_gauges(tracked_gauges, stamp=stamp)

        # finalize
        self.increment_counters()
        self.finalize_gauges()
