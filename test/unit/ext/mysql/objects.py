# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase
from test.fixtures.defaults import DEFAULT_UUID
from amplify.ext.mysql.objects import MySQLObject

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class MySQLObjectTestCase(BaseTestCase):

    def test_init(self):
        mysql_obj = MySQLObject(
            local_id=123,
            pid=2,
            cmd='/usr/sbin/mysqld --basedir=/usr '
                '--datadir=/var/lib/mysql --plugin-dir=/usr/lib/mysql/plugin '
                '--user=mysql --log-error=/var/log/mysql/error.log '
                '--pid-file=/var/run/mysqld/mysqld.pid --socket=/var/run/mysqld/mysqld.sock --port=3306',
            conf_path='/etc/mysql/my.cnf'
        )
        assert_that(mysql_obj, not_none())

        assert_that(mysql_obj.local_id_args, equal_to(
            (
                '/usr/sbin/mysqld --basedir=/usr --datadir=/var/lib/mysql '
                '--plugin-dir=/usr/lib/mysql/plugin --user=mysql '
                '--log-error=/var/log/mysql/error.log --pid-file=/var/run/mysqld/mysqld.pid '
                '--socket=/var/run/mysqld/mysqld.sock --port=3306',
                '/etc/mysql/my.cnf'
            )
        ))
        assert_that(mysql_obj.local_id, equal_to(123))
        assert_that(mysql_obj.definition, equal_to(
            {'local_id': 123, 'type': 'mysql', 'root_uuid': DEFAULT_UUID}
        ))
        assert_that(mysql_obj.definition_hash, equal_to(
            '7b596b9b7d87405fc284244218bff210d16d58d4ebd37d5bd87c1fa61d65c3d2'
        ))
        assert_that(mysql_obj.collectors, has_length(2))
        assert_that(mysql_obj.display_name, is_not(None))
