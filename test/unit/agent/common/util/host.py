# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.common.util import host
from test.base import WithConfigTestCase
from amplify.agent.common.context import context

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class HostTestCase(WithConfigTestCase):
    def test_hostname_uuid_os(self):
        hostname = host.hostname()
        assert_that(hostname, is_not(None))

        uuid = host.uuid()
        assert_that(uuid, is_not(None))

        os_name = host.os_name()
        assert_that(os_name, is_not(None))

    def test_store_uuid_false_with_generated_uuid(self):

        context.app_config.save('credentials', 'store_uuid', False)
        context.app_config.save('credentials', 'uuid', None)
        context._setup_app_config(config_file=self.fake_config_file)
        assert_that(context.app_config['credentials']['store_uuid'], equal_to(False))
        assert_that(context.app_config['credentials']['uuid'], equal_to(None))
        context.uuid = host.uuid()
        context._setup_host_details()
        context._setup_app_config(config_file=self.fake_config_file)
        assert_that(context.app_config['credentials']['uuid'], equal_to(None))

    def test_store_uuid_false_with_uuid_from_config(self):

        context.app_config.save('credentials', 'store_uuid', False)
        context.app_config.save('credentials', 'uuid', 'fakeuuid1')
        context._setup_app_config(config_file=self.fake_config_file)
        assert_that(context.app_config['credentials']['store_uuid'], equal_to(False))
        assert_that(context.app_config['credentials']['uuid'], equal_to('fakeuuid1'))
        context.uuid = host.uuid()
        context._setup_host_details()
        context._setup_app_config(config_file=self.fake_config_file)
        assert_that(context.app_config['credentials']['uuid'], equal_to('fakeuuid1'))

    def test_store_uuid_true_with_generated_uuid(self):

        context.app_config.save('credentials', 'store_uuid', True)
        context.app_config.save('credentials', 'uuid', '')
        context._setup_app_config(config_file=self.fake_config_file)
        assert_that(context.app_config['credentials']['store_uuid'], equal_to(True))
        assert_that(context.app_config['credentials']['uuid'], equal_to(''))
        context.uuid = host.uuid()
        context._setup_host_details()
        context._setup_app_config(config_file=self.fake_config_file)
        assert_that(context.app_config['credentials']['uuid'], is_not(''))

    def test_store_uuid_true_with_uuid_from_config(self):

        context.app_config.save('credentials', 'store_uuid', True)
        context.app_config.save('credentials', 'uuid', 'fakeuuid')
        context._setup_app_config(config_file=self.fake_config_file)
        assert_that(context.app_config['credentials']['store_uuid'], equal_to(True))
        assert_that(context.app_config['credentials']['uuid'], equal_to('fakeuuid'))
        context.uuid = host.uuid()
        context._setup_host_details()
        context._setup_app_config(config_file=self.fake_config_file)
        assert_that(context.app_config['credentials']['uuid'], equal_to('fakeuuid'))

    def test_is_valid_hostname(self):

        assert_that(host.is_valid_hostname('foo.bar'), equal_to(True))
        assert_that(host.is_valid_hostname('abcdefg123-foo.com'), equal_to(True))
        assert_that(host.is_valid_hostname('0f26e87c7df0'), equal_to(True))
        assert_that(host.is_valid_hostname('_foo._tcp.myhostname.com'), equal_to(True))
        assert_that(host.is_valid_hostname('_foo._bar.abc.host.com'), equal_to(True))
        assert_that(host.is_valid_hostname('localhost'), equal_to(False))
        assert_that(host.is_valid_hostname('_foo._bar._foobar.com'), equal_to(False))
        assert_that(host.is_valid_hostname('_foo.bar'), equal_to(False))
        assert_that(host.is_valid_hostname('foo@bar'), equal_to(False))