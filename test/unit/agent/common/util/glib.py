# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

import amplify.agent.common.util.glib as glib


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class GlibTestCase(BaseTestCase):
    def test_overall(self):
        excludes = [
            'access-frontend-*.log',
            'receiver1-*.log',
            'frontend2.log',
            '/var/log/nginx/frontend/*',
            '/var/log/naas/'
        ]

        file_paths = [
            '/var/log/nginx/frontend/asdf.log',  # exclude 4
            '/var/log/nginx/frontend/frontend3.log',  # exclude 4
            '/var/log/blank.log',
            '/var/log/frontend2.log',  # exclude 3
            '/var/receiver1-2012.log',  # exclude 2
            '/var/log/naas/blah.log',  # exclude 5
            'access-frontend-asf.log'  # exclude 1
        ]

        results = file_paths
        for exclude_pathname in excludes:
            for match in glib.glib(file_paths, exclude_pathname):
                results.remove(match)

        assert_that(results, has_length(1))
        assert_that(results[0], equal_to('/var/log/blank.log'))

    def test_more(self):
        pattern = '/etc/nginx/*.conf'

        file_paths = [
            '/etc/nginx/nginx.conf',
            '/etc/nginx/bir/aaa/subdir/host.conf',
            '/etc/nginx/conf.d/blockips.conf',
            '/etc/nginx/conf.d/default.conf',
            '/etc/nginx/conf.d/default.conf.bak',
            '/etc/nginx/conf.d/host.conf',
            '/etc/nginx/conf.d/proxy.conf',
            '/etc/nginx/conf.d/ssl.conf',
            '/etc/nginx/conf.d/servers/bamboo_server.conf',
            '/etc/nginx/conf.d/servers/dev1_server.conf',
            '/etc/nginx/conf.d/servers/dev1db00_server.conf',
            '/etc/nginx/conf.d/servers/docker_build_server.conf',
            '/etc/nginx/conf.d/servers/docker_registry_server.conf',
            '/etc/nginx/conf.d/servers/eurotax_proxy.conf',
            '/etc/nginx/conf.d/servers/int01_server.conf',
            '/etc/nginx/conf.d/servers/int01db00_server.conf',
            '/etc/nginx/conf.d/servers/nexus_server.conf',
            '/etc/nginx/conf.d/servers/soft2run_server.conf',
            '/etc/nginx/conf.d/servers/spearhead_server.conf',
            '/etc/nginx/conf.d/servers/toolsdb_server.conf',
            '/etc/nginx/conf.d/servers/webcache_server.conf.bak',
            '/etc/nginx/conf.d/servers/webcache_server_working.conf',
            '/etc/nginx/conf.d/tcp_streams/iboxdb_server.conf',
            '/etc/nginx/ssl/soft2run_ssl_cert.conf',
            '/etc/nginx/ssl/sph_ssl_cert.conf'
        ]

        results = glib.glib(file_paths, pattern)

        assert_that(results, has_length(1))
        assert_that(results[0], equal_to('/etc/nginx/nginx.conf'))

    def test_more_directories(self):
        pattern = '/etc/nginx/conf.d/*/*.conf'

        file_paths = [
            '/etc/nginx/nginx.conf',
            '/etc/nginx/bir/aaa/subdir/host.conf',
            '/etc/nginx/conf.d/blockips.conf',
            '/etc/nginx/conf.d/default.conf',
            '/etc/nginx/conf.d/default.conf.bak',
            '/etc/nginx/conf.d/host.conf',
            '/etc/nginx/conf.d/proxy.conf',
            '/etc/nginx/conf.d/ssl.conf',
            '/etc/nginx/conf.d/servers/bamboo_server.conf',
            '/etc/nginx/conf.d/servers/dev1_server.conf',
            '/etc/nginx/conf.d/servers/dev1db00_server.conf',
            '/etc/nginx/conf.d/servers/docker_build_server.conf',
            '/etc/nginx/conf.d/servers/docker_registry_server.conf',
            '/etc/nginx/conf.d/servers/eurotax_proxy.conf',
            '/etc/nginx/conf.d/servers/int01_server.conf',
            '/etc/nginx/conf.d/servers/int01db00_server.conf',
            '/etc/nginx/conf.d/servers/nexus_server.conf',
            '/etc/nginx/conf.d/servers/soft2run_server.conf',
            '/etc/nginx/conf.d/servers/spearhead_server.conf',
            '/etc/nginx/conf.d/servers/toolsdb_server.conf',
            '/etc/nginx/conf.d/servers/webcache_server.conf.bak',
            '/etc/nginx/conf.d/servers/webcache_server_working.conf',
            '/etc/nginx/conf.d/tcp_streams/iboxdb_server.conf',
            '/etc/nginx/ssl/soft2run_ssl_cert.conf',
            '/etc/nginx/ssl/sph_ssl_cert.conf'
        ]

        results = glib.glib(file_paths, pattern)

        assert_that(results, has_length(15))

        matches = [
            '/etc/nginx/conf.d/servers/bamboo_server.conf',
            '/etc/nginx/conf.d/servers/dev1_server.conf',
            '/etc/nginx/conf.d/servers/dev1db00_server.conf',
            '/etc/nginx/conf.d/servers/docker_build_server.conf',
            '/etc/nginx/conf.d/servers/docker_registry_server.conf',
            '/etc/nginx/conf.d/servers/eurotax_proxy.conf',
            '/etc/nginx/conf.d/servers/int01_server.conf',
            '/etc/nginx/conf.d/servers/int01db00_server.conf',
            '/etc/nginx/conf.d/servers/nexus_server.conf',
            '/etc/nginx/conf.d/servers/soft2run_server.conf',
            '/etc/nginx/conf.d/servers/spearhead_server.conf',
            '/etc/nginx/conf.d/servers/toolsdb_server.conf',
            '/etc/nginx/conf.d/servers/webcache_server.conf.bak',
            '/etc/nginx/conf.d/servers/webcache_server_working.conf',
            '/etc/nginx/conf.d/tcp_streams/iboxdb_server.conf'
        ]
        for result in results:
            assert_that(result, any_of(*matches))

# TODO: Add more tests for individual instances and edge cases.
