# -*- coding: utf-8 -*-
import time
from copy import deepcopy
from hamcrest import *

from test.unit.ext.mysql.base import MySQLTestCase, MySQLSupervisordTestCase
from amplify.agent.common.context import context
from amplify.ext.mysql.managers import MySQLManager

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class MySQLManagerTestCase(MySQLTestCase):

    def setup_method(self, method):
        super(MySQLManagerTestCase, self).setup_method(method)
        self.original_app_config = deepcopy(context.app_config['mysql'])
        context._setup_object_tank()

    def teardown_method(self, method):
        context._setup_object_tank()
        context.app_config['mysql'] = self.original_app_config
        super(MySQLManagerTestCase, self).teardown_method(method)

    def test_find_local(self):
        mysql_manager = MySQLManager()
        assert_that(mysql_manager, not_none())

        found_masters = mysql_manager._find_local()
        assert_that(found_masters, not_none())
        assert_that(found_masters, has_length(1))

        found_master = found_masters[0]
        assert_that(
            found_master['cmd'],
            equal_to('/usr/sbin/mysqld --basedir=/usr --datadir=/var/lib/mysql '
                     '--plugin-dir=/usr/lib/mysql/plugin --user=mysql '
                     '--log-error=/var/log/mysql/error.log --pid-file=/var/run/mysqld/mysqld.pid '
                     '--socket=/var/run/mysqld/mysqld.sock --port=3306')
        )
        assert_that(
            found_master['conf_path'],
            equal_to('/etc/mysql/my.cnf')
        )
        assert_that(found_master['pid'], not_none())
        assert_that(found_master['local_id'], equal_to(
            'd3780726c2fdcbf45e32729a3113131f1cb4cf9a7cd42f99cd3f0ec88b9840c6'
        ))

    def test_find_correct_cmd(self):
        ps_output = [
            ('17761 1 /usr/sbin/mysqld --basedir=/usr --datadir=/var/lib/mysql --plugin-dir=/usr/lib/mysql/plugin' +
             ' --user=mysql --skip-log-error --open-files-limit=65535 --pid-file=/var/run/mysqld/mysqld.pid' +
             ' --socket=/var/run/mysqld/mysqld.sock --port=3306'),
            ('17764 1 /bin/sh /usr/local/bin/mysqld_safe --basedir=/usr/local --datadir=/var/db/mysql' +
             ' --user=mysql --pid-file=/var/db/mysql/freebsd-amd64-arie-test.pid'),
            '17762 1 logger -t mysqld -p daemon error',
            '17763 1 mysql -u root -p',
            ''
        ]

        # find mysql master processes
        found_masters = MySQLManager()._find_local(ps=ps_output)

        # check that only the first command from the ps output would be recognized as a master process
        assert_that(found_masters, has_length(1))
        assert_that(found_masters[0]['cmd'], equal_to(
            '/usr/sbin/mysqld --basedir=/usr --datadir=/var/lib/mysql --plugin-dir=/usr/lib/mysql/plugin ' +
            '--user=mysql --skip-log-error --open-files-limit=65535 --pid-file=/var/run/mysqld/mysqld.pid ' +
            '--socket=/var/run/mysqld/mysqld.sock --port=3306'
        ))

    def test_discover_objects(self):
        mysql_manager = MySQLManager()
        assert_that(mysql_manager, not_none())

        # check to make sure there are no mysqlds
        mysql_objects = context.objects.find_all(types=mysql_manager.types)
        assert_that(mysql_objects, has_length(0))

        # find objects
        mysql_manager._discover_objects()

        # check to see that a mysqld is found
        mysql_objects = context.objects.find_all(types=mysql_manager.types)
        assert_that(mysql_objects, has_length(1))

    def test_stop_objects(self):
        mysql_manager = MySQLManager()
        assert_that(mysql_manager, not_none())

        # check to make sure there are no mysqlds
        mysql_objects = context.objects.find_all(types=mysql_manager.types)
        assert_that(mysql_objects, has_length(0))

        # find objects
        mysql_manager._discover_objects()

        # check to see that a mysqld is found
        mysql_objects = context.objects.find_all(types=mysql_manager.types)
        assert_that(mysql_objects, has_length(1))

        # stop mysqld
        self.stop_mysqld()

        # re-discover
        mysql_manager._discover_objects()

        # check to make sure there are no mysqlds
        mysql_objects = context.objects.find_all(types=mysql_manager.types)
        assert_that(mysql_objects, has_length(0))

    def test_restart_objects(self):
        mysql_manager = MySQLManager()
        assert_that(mysql_manager, not_none())

        # check to make sure there are no mysqlds
        mysql_objects = context.objects.find_all(types=mysql_manager.types)
        assert_that(mysql_objects, has_length(0))

        # find objects
        mysql_manager._discover_objects()

        # check to see that a mysqld is found
        mysql_objects = context.objects.find_all(types=mysql_manager.types)
        assert_that(mysql_objects, has_length(1))

        # store the mysqld id
        old_master_id = mysql_objects[0].id

        # stop mysqld
        self.stop_mysqld()

        time.sleep(0.1)

        # restart mysqld
        self.start_mysqld()

        time.sleep(0.1)

        # re-discover
        mysql_manager._discover_objects()

        # check to see that a mysql is found
        mysql_objects = context.objects.find_all(types=mysql_manager.types)
        assert_that(mysql_objects, has_length(1))

        master_id = mysql_objects[0].id
        assert_that(master_id, not_(equal_to(old_master_id)))

    def test_find_remote(self):
        mysql_manager = MySQLManager()
        assert_that(mysql_manager, not_none())

        # stop mysqld & set remote mysql to True
        self.stop_mysqld()

        context.app_config['mysql']['remote'] = True

        found_masters = mysql_manager._find_remote()
        assert_that(found_masters, not_none())
        assert_that(found_masters, has_length(1))

        found_master = found_masters[0]
        assert_that(
            found_master['cmd'],
            equal_to('unknown')
        )
        assert_that(
            found_master['conf_path'],
            equal_to('unknown')
        )
        assert_that(found_master['pid'],  equal_to('unknown'))
        assert_that(found_master['local_id'], equal_to(
            'd47bcca34c2b2836266086c5d5d428b754cc4831e2df6e251b2ffa27bca59b3b'
        ))


class SupervisorMySQLManagerTestCase(MySQLManagerTestCase, MySQLSupervisordTestCase):
    pass
