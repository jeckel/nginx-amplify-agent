# -*- coding: utf-8 -*-
import requests_mock
import time

from copy import deepcopy
from hamcrest import *

from amplify.agent.common.context import context
from amplify.agent.supervisor import Supervisor
from amplify.agent.common.errors import AmplifyCriticalException
from test.base import RealNginxTestCase, nginx_plus_test, nginx_oss_test
from test.fixtures.defaults import DEFAULT_API_URL, DEFAULT_API_KEY

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class SupervisorTestCase(RealNginxTestCase):

    def setup_method(self, method):
        super(SupervisorTestCase, self).setup_method(method)
        self.old_cloud_config = deepcopy(context.app_config.config)
        self.old_backpressure_time = context.backpressure_time

    def teardown_method(self, method):
        context.app_config.config = self.old_cloud_config
        context.backpressure_time = self.old_backpressure_time
        super(SupervisorTestCase, self).teardown_method(method)

    def test_talk_to_cloud(self):
        """
        Checks that we apply all changes from cloud to agent config and object configs
        """
        supervisor = Supervisor()

        supervisor.init_object_managers()
        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        old_object_configs = deepcopy(supervisor.object_managers['nginx'].object_configs)

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            old_restart_time = supervisor.last_cloud_talk_restart
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        assert_that(supervisor.last_cloud_talk_restart, not_(equal_to(old_restart_time)))

        # check that agent config was changed
        assert_that(context.app_config.config, not_(equal_to(self.old_cloud_config)))

        # check that object configs were also changed
        nginx_manager = supervisor.object_managers['nginx']
        assert_that(nginx_manager.object_configs, not_(equal_to(old_object_configs)))

    def test_talk_to_cloud_no_change(self):
        """
        Checks that we apply all changes from cloud to agent config and object configs
        """
        supervisor = Supervisor()

        supervisor.init_object_managers()
        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # first talk change
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        time.sleep(1)

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # second talk no change
            old_restart_time = deepcopy(supervisor.last_cloud_talk_restart)
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        assert_that(supervisor.last_cloud_talk_restart, equal_to(old_restart_time))

    def test_talk_to_cloud_container_change(self):
        """
        Checks that we detect changes from manager
        """
        supervisor = Supervisor()

        # TODO: managers -> nginx -> run_test must be in this order
        #       (true/false rather than false/true) breaks this test.

        supervisor.init_object_managers()
        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # first talk change
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        time.sleep(1)

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # second talk no change
            old_restart_time = deepcopy(supervisor.last_cloud_talk_restart)
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        assert_that(supervisor.last_cloud_talk_restart, equal_to(old_restart_time))

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": false, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            old_object_configs = deepcopy(supervisor.object_managers['nginx'].object_configs)

            time.sleep(1)

            # third talk change to manager only
            old_restart_time = deepcopy(supervisor.last_cloud_talk_restart)
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        assert_that(supervisor.last_cloud_talk_restart, not_(equal_to(old_restart_time)))

        # check that object configs not changed
        nginx_manager = supervisor.object_managers['nginx']
        assert_that(nginx_manager.object_configs, equal_to(old_object_configs))

    def test_talk_to_cloud_object_change(self):
        """
        Checks that we detect changes from objects
        """
        supervisor = Supervisor()

        supervisor.init_object_managers()
        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # first talk change
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        time.sleep(1)

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # second talk no change
            old_restart_time = deepcopy(supervisor.last_cloud_talk_restart)
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        assert_that(supervisor.last_cloud_talk_restart, equal_to(old_restart_time))

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":false}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            old_object_configs = deepcopy(supervisor.object_managers['nginx'].object_configs)

            time.sleep(1)

            # third talk change to object only
            old_restart_time = deepcopy(supervisor.last_cloud_talk_restart)
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        assert_that(supervisor.last_cloud_talk_restart, not_(equal_to(old_restart_time)))

        # check that object configs changed
        nginx_manager = supervisor.object_managers['nginx']
        assert_that(nginx_manager.object_configs, not_(equal_to(old_object_configs)))

    def test_change_overdetect(self):
        """
        Checks that we detect changes from manager
        """
        supervisor = Supervisor()

        supervisor.init_object_managers()
        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": false, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # first talk change
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        time.sleep(1)

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": false, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # second talk no change
            old_restart_time = deepcopy(supervisor.last_cloud_talk_restart)
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        assert_that(supervisor.last_cloud_talk_restart, equal_to(old_restart_time))

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            old_object_configs = deepcopy(supervisor.object_managers['nginx'].object_configs)

            time.sleep(1)

            # third talk change to manager only
            old_restart_time = deepcopy(supervisor.last_cloud_talk_restart)
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        assert_that(supervisor.last_cloud_talk_restart, not_(equal_to(old_restart_time)))

        # check that object configs not changed
        nginx_manager = supervisor.object_managers['nginx']
        assert_that(nginx_manager.object_configs, equal_to(old_object_configs))

    def test_backpressure(self):
        """
        Checks that we catch and apply backpressure delay correctly from 503 status codes.
        """
        supervisor = Supervisor()

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                status_code=503,
                text='60.0'
            )

            now = time.time()

            # talk to get delay
            try:
                supervisor.talk_to_cloud(force=True)
            except AmplifyCriticalException:
                pass

            # check that context.backpressure_time was changed
            assert_that(context.backpressure_time, not_(equal_to(self.old_backpressure_time)))
            assert_that(context.backpressure_time, greater_than_or_equal_to(int(now + 60.0)))

    def test_backpressure_ordinal_503(self):
        """
        Checks that the agent doesn't crash on non-formalized 503
        """
        supervisor = Supervisor()

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                status_code=503,
                text='foo'
            )

            now = time.time()

            # talk to get delay
            try:
                supervisor.talk_to_cloud(force=True)
            except AmplifyCriticalException:
                pass

            # check that context.backpressure_time was changed to default 60
            assert_that(context.backpressure_time, not_(equal_to(self.old_backpressure_time)))
            assert_that(context.backpressure_time, greater_than_or_equal_to(int(now + 60.0)))

    def test_filters_unchanged(self):
        """
        Checks that agent is able to determine filters changes
        """
        supervisor = Supervisor()

        supervisor.init_object_managers()
        for object_manager_name in supervisor.object_manager_order:
            object_manager = supervisor.object_managers[object_manager_name]
            object_manager._discover_objects()
        old_nginx_configs = deepcopy(supervisor.object_managers['nginx'].object_configs)

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 60.0, "talk_interval": 60.0, "api_timeout": 15.0}, "containers": {"nginx": {"parse_delay": 0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "root_uuid": "6789abcde", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # talk 1st time - everything changes
            supervisor.talk_to_cloud(force=True)

        for manager in supervisor.object_managers.itervalues():
            manager._discover_objects()

        # check that agent config was changed
        assert_that(context.app_config.config, not_(equal_to(self.old_cloud_config)))
        self.old_cloud_config = deepcopy(context.app_config.config)

        # check that object configs were also changed (because filters were pushed)
        nginx_manager = supervisor.object_managers['nginx']
        assert_that(nginx_manager.object_configs, not_(equal_to(old_nginx_configs)))

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 60.0, "talk_interval": 60.0, "api_timeout": 15.0}, "containers": {"nginx": {"parse_delay": 0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "root_uuid": "6789abcde", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            # talk 2nd time - changes again (filters)
            supervisor.talk_to_cloud(force=True)
            for object_manager_name in supervisor.object_manager_order:
                object_manager = supervisor.object_managers[object_manager_name]
                object_manager._discover_objects()

            # save some vars to check later
            old_nginx_configs = deepcopy(nginx_manager.object_configs)
            nginx_object_init_time = supervisor.object_managers['nginx'].objects.objects[4].init_time

            time.sleep(2)

            # talk 3nd time - no change
            supervisor.talk_to_cloud(force=True)

        for object_manager_name in supervisor.object_manager_order:
            object_manager = supervisor.object_managers[object_manager_name]
            object_manager._discover_objects()

        # check that agent config was not changed
        assert_that(context.app_config.config, equal_to(self.old_cloud_config))

        # check that object configs were not changed
        nginx_manager = supervisor.object_managers['nginx']
        assert_that(nginx_manager.object_configs, equal_to(old_nginx_configs))

        # check that we still use previously created objects
        print supervisor.object_managers['nginx'].objects.objects
        assert_that(
            supervisor.object_managers['nginx'].objects.objects[4].init_time,
            equal_to(nginx_object_init_time)
        )

    @nginx_plus_test
    def test_filters_applying_plus(self):
        self.mock_request_data = '{"config": {"cloud": {"push_interval": 60.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "root_uuid": "6789abcde", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
        self.run_filters_applying_test()

    @nginx_oss_test
    def test_filters_applying_oss(self):
        self.mock_request_data = '{"config": {"cloud": {"push_interval": 60.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"parse_delay": 0, "max_test_duration": 30.0, "run_test": true, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "root_uuid": "6789abcde", "local_id": "151d8728e792f42e129337573a21bb30ab3065d59102f075efc2ded28e713ff8"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
        self.run_filters_applying_test()

    def run_filters_applying_test(self):
        supervisor = Supervisor()

        supervisor.init_object_managers()
        for manager_name in supervisor.object_manager_order:
            supervisor.object_managers[manager_name]._discover_objects()
        nginx_manager = supervisor.object_managers['nginx']
        nginx_obj = nginx_manager.objects.find_all(types=nginx_manager.types)[0]
        assert_that(nginx_obj.filters, has_length(0))

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text=self.mock_request_data
            )

            # talk 1st time
            supervisor.talk_to_cloud(force=True)

        for manager_name in supervisor.object_manager_order:
            supervisor.object_managers[manager_name]._discover_objects()

        nginx_manager = supervisor.object_managers['nginx']
        nginx_obj = nginx_manager.objects.find_all(types=nginx_manager.types)[0]

        assert_that(nginx_obj.filters, has_length(1))

    def test_load_ext_managers(self):
        supervisor = Supervisor()
        assert_that(supervisor.object_managers, has_length(0))

        # load regular ones
        supervisor.init_object_managers()
        assert_that(supervisor.object_managers, has_length(4))

        # load external ones
        supervisor.load_ext_managers()
        assert_that(supervisor.object_managers, has_length(7))

    def test_dont_load_missing_ext_managers(self):
        old = context.app_config.config['extensions']
        context.app_config.config['extensions'] = {}

        supervisor = Supervisor()
        assert_that(supervisor.object_managers, has_length(0))

        # load regular ones
        supervisor.init_object_managers()
        assert_that(supervisor.object_managers, has_length(4))

        # load external ones
        supervisor.load_ext_managers()
        assert_that(supervisor.object_managers, has_length(4))  # non loaded

        context.app_config.config['extensions'] = old

    def test_dont_load_false_ext_managers(self):
        old = context.app_config.config['extensions']
        context.app_config.config['extensions'] = dict(phpfpm=False)

        supervisor = Supervisor()
        assert_that(supervisor.object_managers, has_length(0))

        # load regular ones
        supervisor.init_object_managers()
        assert_that(supervisor.object_managers, has_length(4))

        # load external ones
        supervisor.load_ext_managers()
        assert_that(supervisor.object_managers, has_length(4))  # none loaded

        context.app_config.config['extensions'] = old

    def test_dont_load_string_false_ext_managers(self):
        old = context.app_config.config['extensions']
        context.app_config.config['extensions'] = dict(phpfpm='False')

        supervisor = Supervisor()
        assert_that(supervisor.object_managers, has_length(0))

        # load regular ones
        supervisor.init_object_managers()
        assert_that(supervisor.object_managers, has_length(4))

        # load external ones
        supervisor.load_ext_managers()
        assert_that(supervisor.object_managers, has_length(4))  # none loaded

        context.app_config.config['extensions'] = old

    def test_freeze_api_url_true(self):
        context.freeze_api_url = True
        supervisor = Supervisor()
        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"talk_interval": 120.0, "api_url": "https://receiver.amplify.nginx.com:443/1.3", "push_interval": 60.0, "api_timeout": 10.0}, "containers": {"plus": {"poll_intervals": {"metrics": 20.0, "meta": 60.0, "discover": 10.0}}, "nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 60.0, "logs": 10.0, "discover": 10.0}}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 60.0, "discover": 10.0}}}}, "objects": [{"object": {"type": "nginx", "root_uuid": "6789abcde", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config": {"upload_ssl": true}, "filters": [{"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]}]}], "messages": [], "versions": {"current": 0.41, "old": 0.26, "obsolete": 0.21}}'
            )
            # check that talking to cloud changes the api_url
            assert_that(context.app_config['cloud']['api_url'], equal_to(DEFAULT_API_URL))
            supervisor.talk_to_cloud(force=True)
            assert_that(context.app_config['cloud']['api_url'], equal_to(DEFAULT_API_URL))

    def test_freeze_api_url_false(self):
        context.freeze_api_url = False
        supervisor = Supervisor()
        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"talk_interval": 120.0, "api_url": "https://receiver.amplify.nginx.com:443/1.3", "push_interval": 60.0, "api_timeout": 10.0}, "containers": {"plus": {"poll_intervals": {"metrics": 20.0, "meta": 60.0, "discover": 10.0}}, "nginx": {"parse_delay": 60.0, "max_test_duration": 30.0, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 60.0, "logs": 10.0, "discover": 10.0}}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 60.0, "discover": 10.0}}}}, "objects": [{"object": {"type": "nginx", "root_uuid": "6789abcde", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config": {"upload_ssl": true}, "filters": [{"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [["$request_uri", "~", "/api/timeseries"]]}]}], "messages": [], "versions": {"current": 0.41, "old": 0.26, "obsolete": 0.21}}'
            )
            # check that talking to cloud does not change the api_url
            assert_that(context.app_config['cloud']['api_url'], equal_to(DEFAULT_API_URL))
            supervisor.talk_to_cloud(force=True)
            assert_that(context.app_config['cloud']['api_url'], equal_to('https://receiver.amplify.nginx.com:443/1.3'))
