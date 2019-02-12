# -*- coding: utf-8 -*-
import copy
import os
import shutil
import time

from hamcrest import *

from amplify.agent.common.context import context
from amplify.agent.managers.nginx import NginxManager
from amplify.agent.objects.nginx.object import NginxObject
from amplify.agent.collectors.nginx.config import NginxConfigCollector
from amplify.agent.objects.nginx.config.config import NginxConfig
from test.base import RealNginxTestCase, RealNginxTempFileTestCase, disabled_test, nginx_plus_test
from test.helpers import count_calls

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class NginxObjectTestCase(RealNginxTestCase):

    def setup_method(self, method):
        super(NginxObjectTestCase, self).setup_method(method)

        # same some methods and values so they can be altered inside of tests
        self.original_app_config_nginx = copy.deepcopy(context.app_config['nginx'])
        self.original_app_config_containers = copy.deepcopy(context.app_config['containers'])
        self.original_setup_config_collector = NginxObject._setup_config_collector
        self.original_restore_config_collector = NginxObject._restore_config_collector
        self.original_parse_config = NginxConfigCollector.parse_config
        self.original_full_parse = NginxConfig.full_parse

        # create default dir
        try:
            os.mkdir('/usr/share/nginx/logs/')
        except:
            pass

        # create default logs
        with open('/usr/share/nginx/logs/access.log', 'a'):  # default access log
            os.utime('/usr/share/nginx/logs/access.log', (1, 1))
        with open('/usr/share/nginx/logs/error.log', 'a'):  # default error log
            os.utime('/usr/share/nginx/logs/error.log', (1, 1))

    def teardown_method(self, method):
        # restore original methods and values that were saved
        context.app_config['nginx'] = self.original_app_config_nginx
        context.app_config['containers'] = self.original_app_config_containers
        NginxObject._setup_config_collector = self.original_setup_config_collector
        NginxObject._restore_config_collector = self.original_restore_config_collector
        NginxConfigCollector.parse_config = self.original_parse_config
        NginxConfig.full_parse = self.original_full_parse

        # remove default dir
        shutil.rmtree('/usr/share/nginx/logs/')

        super(NginxObjectTestCase, self).teardown_method(method)

    @nginx_plus_test
    def test_plus_status_discovery(self):
        """
        Checks that for plus nginx we collect two status urls:
        - one for web link (with server name)
        - one for agent purposes (local url)
        """
        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.objects_by_type[manager.type], has_length(1))

        # get nginx object
        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]

        # check all plus status urls
        assert_that(nginx_obj.plus_status_enabled, equal_to(True))
        assert_that(nginx_obj.plus_status_internal_url, equal_to('https://127.0.0.1:443/plus_status'))
        assert_that(nginx_obj.plus_status_external_url, equal_to('https://status.naas.nginx.com:443/plus_status_bad'))

    @nginx_plus_test
    def test_api_discovery(self):
        """
        Checks that for plus nginx we collect two status urls:
        - one for web link (with server name)
        - one for agent purposes (local url)
        """
        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.objects_by_type[manager.type], has_length(1))

        # get nginx object
        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]

        # check all plus status urls
        assert_that(nginx_obj.api_enabled, equal_to(True))
        assert_that(nginx_obj.api_internal_url, equal_to('https://127.0.0.1:443/api'))
        assert_that(nginx_obj.api_external_url, equal_to('https://status.naas.nginx.com:443/api_bad'))

    @nginx_plus_test
    def test_bad_plus_status_discovery(self):
        self.stop_first_nginx()
        self.start_second_nginx(conf='nginx_bad_status.conf')
        manager = NginxManager()
        manager._discover_objects()

        assert_that(manager.objects.objects_by_type[manager.type], has_length(1))

        # get nginx object
        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]

        # check all plus status urls
        assert_that(nginx_obj.plus_status_enabled, equal_to(True))
        assert_that(nginx_obj.plus_status_internal_url, none())
        assert_that(nginx_obj.plus_status_external_url, equal_to('http://bad.status.naas.nginx.com:82/plus_status'))

    @nginx_plus_test
    def test_bad_plus_status_discovery_with_config(self):
        context.app_config['nginx']['plus_status'] = '/foo_plus'
        context.app_config['nginx']['stub_status'] = '/foo_basic'

        self.stop_first_nginx()
        self.start_second_nginx(conf='nginx_bad_status.conf')
        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.objects_by_type[manager.type], has_length(1))

        # self.http_request should look like this
        # [
        # first - internal plus statuses
        # 'http://127.0.0.1:82/plus_status', 'https://127.0.0.1:82/plus_status',
        # 'http://127.0.0.1/foo_plus', 'https://127.0.0.1/foo_plus',
        #
        # then external plus statuses
        # 'http://bad.status.naas.nginx.com:82/plus_status', 'https://bad.status.naas.nginx.com:82/plus_status',
        #
        # finally - stub statuses
        # 'http://127.0.0.1:82/basic_status', 'https://127.0.0.1:82/basic_status',
        # 'http://127.0.0.1/foo_basic', 'https://127.0.0.1/foo_basic'
        # ]

        assert_that(self.http_requests[2], equal_to('http://127.0.0.1/foo_plus'))
        assert_that(self.http_requests[-2], equal_to('http://127.0.0.1/foo_basic'))

    def test_bad_stub_status_discovery_with_config(self):
        context.app_config['nginx']['stub_status'] = '/foo_basic'

        self.stop_first_nginx()
        self.start_second_nginx(conf='nginx_bad_status.conf')
        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.objects_by_type[manager.type], has_length(1))

        assert_that(self.http_requests[-1], equal_to('https://127.0.0.1/foo_basic'))
        assert_that(self.http_requests[-2], equal_to('http://127.0.0.1/foo_basic'))

    def test_skip_parse_on_reload(self):
        # wrap NginxConfig.full_parse with a method that counts how many times it's been called
        NginxConfig.full_parse = count_calls(NginxConfig.full_parse)
        assert_that(NginxConfig.full_parse.call_count, equal_to(0))

        manager = NginxManager()
        manager._discover_objects()

        # check that the config has only been parsed once (at startup)
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(NginxConfig.full_parse.call_count, equal_to(1))

        # reload nginx and discover objects again so manager will recognize it
        self.reload_nginx()
        time.sleep(2)
        manager._discover_objects()

        # metrics collector will cause the nginx object to need a restart because pids have changed
        metrics_collector = nginx_obj.collectors[2]
        metrics_collector.collect(no_delay=True)
        manager._discover_objects()

        # check that the config was not parsed again after the restart
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(NginxConfig.full_parse.call_count, equal_to(1))

        # check that the new nginx object's config collector won't call full_parse
        config_collector = nginx_obj.collectors[0]
        config_collector.collect(no_delay=True)
        assert_that(NginxConfig.full_parse.call_count, equal_to(1))

        # check that the config collector will still call full parse if config changes
        config_collector.previous['files'] = {}
        config_collector.collect(no_delay=True)
        assert_that(NginxConfig.full_parse.call_count, equal_to(2))

    def test_upload_ssl(self):
        context.app_config['containers']['nginx']['upload_ssl'] = True
        manager = NginxManager()
        manager._discover_objects()

        # check that the config has only been parsed once (at startup)
        nginx_obj = manager.objects.find_all(types=manager.types)[0]

        assert_that(nginx_obj.upload_ssl, equal_to(True))
        assert_that(nginx_obj.config.ssl_certificates, has_length(1))

    def test_skip_upload_ssl(self):
        context.app_config['containers']['nginx']['upload_ssl'] = False
        manager = NginxManager()
        manager._discover_objects()

        # check that the config has only been parsed once (at startup)
        nginx_obj = manager.objects.find_all(types=manager.types)[0]

        assert_that(nginx_obj.upload_ssl, equal_to(False))
        assert_that(nginx_obj.config.ssl_certificates, has_length(0))

    # TODO: Fill out these tests once we move our test containers to Ubuntu 16.04
    @disabled_test
    def test_start_syslog_listener(self):
        pass

    @disabled_test
    def test_not_start_syslog_listener(self):
        pass

    def test_with_default_logs(self):
        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.objects_by_type[manager.type], has_length(1))

        # get nginx object
        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]

        # just check that everything went ok
        assert_that(nginx_obj, not_none())

    def test_preserve_parse_errors_after_object_reload(self):
        self.start_first_nginx()
        manager = NginxManager()
        manager._discover_objects()

        # check that the config after parsing has no errors
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        nginx_obj.config.full_parse()
        assert_that(nginx_obj.config.parser_errors, has_length(0))

        nginx_obj.config.parser_errors.append('failed to parse /etc/nginx/nginx.conf')

        # reload nginx and discover objects again
        self.reload_nginx()
        time.sleep(1)
        manager._discover_objects()

        # check that nginx object eventd has expected error after reload
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        messages = [event.message for event in nginx_obj.eventd.current.values()]
        assert_that(messages, has_item(starts_with('failed to parse /etc/nginx/nginx.conf')))

    def test_preserve_parse_errors_after_object_restart(self):
        self.start_first_nginx()
        manager = NginxManager()
        manager._discover_objects()

        # check that the config after parsing has no errors
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        nginx_obj.config.full_parse()
        assert_that(nginx_obj.config.parser_errors, has_length(0))

        nginx_obj.config.parser_errors.append('failed to parse /etc/nginx/nginx.conf')
        nginx_obj.need_restart = True
        # restart nginx and discover objects again
        self.restart_nginx()
        time.sleep(1)
        manager._discover_objects()

        # check that nginx object has parse errors after reload
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        messages = [event.message for event in nginx_obj.eventd.current.values()]
        assert_that(messages, has_item(starts_with('failed to parse /etc/nginx/nginx.conf')))

    def test_restore_config_collector(self):
        # begin counting the number of calls of these two methods
        NginxObject._setup_config_collector = count_calls(NginxObject._setup_config_collector)
        NginxObject._restore_config_collector = count_calls(NginxObject._restore_config_collector)
        NginxConfigCollector.parse_config = count_calls(NginxConfigCollector.parse_config)
        NginxConfig.full_parse = count_calls(NginxConfig.full_parse)

        # confirm that all the call counts start at zero
        assert_that(NginxObject._setup_config_collector.call_count, equal_to(0))
        assert_that(NginxObject._restore_config_collector.call_count, equal_to(0))
        assert_that(NginxConfigCollector.parse_config.call_count, equal_to(0))
        assert_that(NginxConfig.full_parse.call_count, equal_to(0))

        manager = NginxManager()
        manager._discover_objects()

        # check that nginx object was initialized but not from restart
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(nginx_obj.need_restart, equal_to(False))
        assert_that(nginx_obj.collectors[0].short_name, equal_to('nginx_config'))
        assert_that(nginx_obj.data, not_(has_key('config_data')))  # no previous config data

        # check that _setup_config_collector and not _restore_config_collector
        assert_that(NginxObject._setup_config_collector.call_count, equal_to(1))
        assert_that(NginxObject._restore_config_collector.call_count, equal_to(0))
        # check parse_config was called inside _setup_config_collector and that full_parse was run
        assert_that(NginxConfigCollector.parse_config.call_count, equal_to(1))
        assert_that(NginxConfig.full_parse.call_count, equal_to(1))

        # restart nginx and discover objects again
        nginx_obj.need_restart = True
        manager._discover_objects()

        # check that nginx object was initialized by restarting nginx that already had run parse_config once
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(nginx_obj.need_restart, equal_to(False))
        assert_that(nginx_obj.collectors[0].short_name, equal_to('nginx_config'))
        assert_that(nginx_obj.data, has_entries({
            'config_data': has_entries({
                'previous': has_entries({
                    'files': instance_of(dict)  # found by NginxConfigCollector.parse_config
                })
            })
        }))
        # check that _restore_config_collector was called instead of _setup_config_collector
        assert_that(NginxObject._setup_config_collector.call_count, equal_to(1))
        assert_that(NginxObject._restore_config_collector.call_count, equal_to(1))
        # check parse_config was called inside _restore_config_collector but full_parse was skipped
        assert_that(NginxConfigCollector.parse_config.call_count, equal_to(2))
        assert_that(NginxConfig.full_parse.call_count, equal_to(1))


class NginxObjectTempFileTestCase(RealNginxTempFileTestCase):

    def test_add_config_error_then_reload(self):
        manager = NginxManager()
        manager._discover_objects()
        nginx_objects = manager.objects.find_all(types=manager.types)
        assert_that(nginx_objects, has_length(0))

        # write the initial good config and start running nginx (should work)
        self.write_config(
            'events {}'
            'http {'
            '    server {'
            '        location /status {stub_status on;}'
            '    }'
            '}'
        )
        self.start_nginx(check=True)

        # check that nginx object was created and then run its config collector
        manager._discover_objects()
        nginx_objects = manager.objects.find_all(types=manager.types)
        assert_that(nginx_objects, has_length(1))
        nginx_obj = nginx_objects[0]

        # store some values from before the bad reload for testing purposes later
        before_bad_reload_config_subtree = nginx_obj.config.subtree
        before_bad_reload_config_stub_status_urls = nginx_obj.config.stub_status_urls
        before_bad_reload_object_workers = nginx_obj.workers
        before_bad_reload_object_stub_status_url = nginx_obj.stub_status_url
        before_bad_reload_object_api_endpoints_to_skip = nginx_obj.api_endpoints_to_skip

        # introduce an error to the config and try to reload nginx (should not work)
        self.write_config(
            'events {{{{{{{{{}'
            'http {'
            '    server {'
            '        location /status {stub_status on;}'
            '    }'
            '}'
        )
        self.reload_nginx(check=False)

        # run the config collector again now that the config has errors in it
        # collect manually because the nginx object shouldn't have restarted so it wouldn't parse on restore
        manager._discover_objects()
        nginx_objects = manager.objects.find_all(types=manager.types)
        assert_that(nginx_objects, has_length(1))
        nginx_obj = nginx_objects[0]
        nginx_obj.collectors[0].collect(no_delay=True)

        # check that the nginx process did not reload but the NginxConfig object did parse and update
        assert_that(before_bad_reload_object_workers, equal_to(nginx_obj.workers))
        assert_that(before_bad_reload_config_subtree, has_length(2))
        assert_that(before_bad_reload_config_stub_status_urls, has_length(2))
        assert_that(nginx_obj.config.subtree, has_length(0))  # when too many "{" in file subtree is empty
        assert_that(nginx_obj.config.stub_status_urls, has_length(0))

        # check that although the NginxConfig parsed and updated, the NginxObject kept its cached data
        assert_that(before_bad_reload_object_stub_status_url, equal_to(nginx_obj.stub_status_url))
        assert_that(before_bad_reload_object_api_endpoints_to_skip, equal_to(nginx_obj.api_endpoints_to_skip))
