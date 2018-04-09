# -*- coding: utf-8 -*-
from hamcrest import *

from test.unit.ext.mysql.base import MySQLTestCase
from test.fixtures.defaults import DEFAULT_UUID
from amplify.agent.common.context import context
from amplify.ext.mysql.managers import MySQLManager
from amplify.ext.mysql.collectors.meta import MySQLMetaCollector

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class MySQLMetaCollectorTestCase(MySQLTestCase):

    def setup_method(self, method):
        super(MySQLMetaCollectorTestCase, self).setup_method(method)
        context._setup_object_tank()

        mysql_manager = MySQLManager()
        mysql_manager._discover_objects()
        found_objects = context.objects.find_all(types=mysql_manager.types)

        self.mysql_object = found_objects[0]

    def teardown_method(self, method):
        context._setup_object_tank()
        super(MySQLMetaCollectorTestCase, self).teardown_method(method)

    def test_init(self):
        mysql_meta_collector = MySQLMetaCollector(
            object=self.mysql_object, interval=self.mysql_object.intervals['meta']
        )
        assert_that(mysql_meta_collector, not_none())
        assert_that(mysql_meta_collector, is_(MySQLMetaCollector))

    def test_collect(self):
        mysql_meta_collector = MySQLMetaCollector(
            object=self.mysql_object, interval=self.mysql_object.intervals['meta']
        )
        assert_that(mysql_meta_collector, not_none())

        # make sure meta is empty
        assert_that(mysql_meta_collector.meta, equal_to({}))

        # collect and assert that meta is not empty
        mysql_meta_collector.collect()

        # collect twice in case bin_path found second
        mysql_meta_collector.collect()

        # check value
        assert_that(mysql_meta_collector.meta, has_entries(
            {
                'display_name': 'mysql @ hostname.nginx',
                'local_id': 'd3780726c2fdcbf45e32729a3113131f1cb4cf9a7cd42f99cd3f0ec88b9840c6',
                'type': 'mysql',
                'cmd': '/usr/sbin/mysqld '
                       '--basedir=/usr --datadir=/var/lib/mysql '
                       '--plugin-dir=/usr/lib/mysql/plugin --user=mysql '
                       '--log-error=/var/log/mysql/error.log '
                       '--pid-file=/var/run/mysqld/mysqld.pid '
                       '--socket=/var/run/mysqld/mysqld.sock --port=3306',
                'pid': self.mysql_object.pid,
                'conf_path': '/etc/mysql/my.cnf',
                'root_uuid': DEFAULT_UUID,
                'bin_path': '/usr/sbin/mysqld',
                'version': starts_with('5.5'),
                'version_line': starts_with('/usr/sbin/mysqld  Ver 5.5')
            }
        ))

        # check that it matches the object metad
        assert_that(
            mysql_meta_collector.meta,
            equal_to(self.mysql_object.metad.current)
        )
