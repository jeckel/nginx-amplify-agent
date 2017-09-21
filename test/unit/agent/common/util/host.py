# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.common.util import host
from test.base import WithConfigTestCase

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
