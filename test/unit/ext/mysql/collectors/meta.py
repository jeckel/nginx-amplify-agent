# -*- coding: utf-8 -*-
from hamcrest import *
from copy import deepcopy

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
        self.old = deepcopy(context.app_config['mysql'])
        context._setup_object_tank()

        mysql_manager = MySQLManager()
        mysql_manager._discover_objects()
        found_objects = context.objects.find_all(types=mysql_manager.types)

        self.mysql_object = found_objects[0]

    def teardown_method(self, method):
        context._setup_object_tank()
        context.app_config['mysql'] = self.old
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
                'connection_location': '/var/run/mysqld/mysqld.sock',
                'version': starts_with('5.5'),
            }
        ))

    def test_mysql_version(self):
        mysql_meta_collector = MySQLMetaCollector(
            object=self.mysql_object, interval=self.mysql_object.intervals['meta']
        )
        assert_that(mysql_meta_collector, not_none())
        assert_that(mysql_meta_collector.meta, equal_to({}))

        assert_that(mysql_meta_collector._version, equal_to(None))

        mysql_meta_collector.version()

        assert_that(mysql_meta_collector._version, starts_with('5.5'))
        assert_that('-', not_(is_in(mysql_meta_collector._version)))
        assert_that(mysql_meta_collector._version.replace('.', '').isdigit(), equal_to(True))

    def test_mysql_connection_location(self):
        mysql_meta_collector = MySQLMetaCollector(
            object=self.mysql_object, interval=self.mysql_object.intervals['meta']
        )
        assert_that(mysql_meta_collector, not_none())
        assert_that(mysql_meta_collector.meta, equal_to({}))

        assert_that(mysql_meta_collector._connection_location, equal_to(None))

        mysql_meta_collector.connection_location()

        assert_that(mysql_meta_collector._connection_location, equal_to('/var/run/mysqld/mysqld.sock'))

        context.app_config['mysql']['remote'] = True
        context.app_config['mysql']['host'] = "localhost"
        context.app_config['mysql']['port'] = "1234"
        context.app_config['mysql']['unix_socket'] = None

        mysql_meta_collector.connection_location()
        assert_that(mysql_meta_collector._connection_location, equal_to('localhost:1234'))

        context.app_config['mysql']['host'] = "127.0.0.1"
        context.app_config['mysql']['port'] = None

        mysql_meta_collector.connection_location()
        assert_that(mysql_meta_collector._connection_location, equal_to('127.0.0.1'))

    def test_collect_remote(self):
        context.app_config['mysql']['remote'] = True
        context.app_config['mysql']['host'] = '127.0.0.1'
        context.app_config['mysql']['port'] = '3306'
        context.app_config['mysql'].pop('unix_socket', None)
        mysql_manager = MySQLManager()
        mysql_manager._discover_objects()
        found_objects = context.objects.find_all(types=mysql_manager.types)

        self.mysql_object = found_objects[0]
        mysql_meta_collector = MySQLMetaCollector(
            object=self.mysql_object, interval=self.mysql_object.intervals['meta']
        )

        # collect and assert that meta is not empty
        mysql_meta_collector.collect()

        # check value
        assert_that(mysql_meta_collector.meta, has_entries(
            {
                'display_name': 'mysql @ hostname.nginx',
                'local_id': 'd47bcca34c2b2836266086c5d5d428b754cc4831e2df6e251b2ffa27bca59b3b',
                'type': 'mysql',
                'cmd': 'unknown',
                'pid': 'unknown',
                'conf_path': 'unknown',
                'root_uuid': DEFAULT_UUID,
                'bin_path': 'unknown',
                'connection_location': '127.0.0.1:3306',
                'version': starts_with('5.5'),
            }
        ))

        # check that it matches the object metad
        assert_that(
            mysql_meta_collector.meta,
            equal_to(self.mysql_object.metad.current)
        )
