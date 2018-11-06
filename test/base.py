# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all(socket=False, subprocess=True, ssl=False)

import os
import imp
import pytest
import random
import shutil
import time
import copy

from unittest import TestCase

import test.unit.agent.common.config.app

from amplify.agent.common.util import configreader, subp, host
from amplify.agent.common.errors import AmplifySubprocessError
from amplify.agent.common.context import context
from amplify.agent.objects.abstract import AbstractObject
from amplify.agent.tanks.config import ConfigTank

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class BaseTestCase(TestCase):
    def setup_method(self, method):
        imp.reload(configreader)
        imp.reload(test.unit.agent.common.config.app)

        # remove reference to Singleton for GC
        context.setup(
            app='test',
            app_config=test.unit.agent.common.config.app.TestingConfig(),
            agent_name='amplify'
        )
        context.setup_thread_id()

        context.default_log.info(
            '%s %s::%s %s' % ('=' * 20, self.__class__.__name__, self._testMethodName, '=' * 20)
        )

        # modify http client to store http requests
        from amplify.agent.common.util.http import HTTPClient
        self.http_requests = []

        original_get = HTTPClient.get
        original_post = HTTPClient.post

        def fake_get(obj, url, *args, **kwargs):
            self.http_requests.append(url)
            return original_get(obj, url, *args, **kwargs)

        def fake_post(obj, url, *args, **kwargs):
            self.http_requests.append(url)
            return original_post(obj, url, *args, **kwargs)

        HTTPClient.get = fake_get
        HTTPClient.post = fake_post

        import amplify.agent.pipelines.file
        amplify.agent.pipelines.file.OFFSET_CACHE = {}

    def teardown_method(self, method):
        pass


class BaseControllerTestCase(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self):
        """
        this reloads the top level modules so that everything is
        reloaded with new context.

        Eg: reload IGNORE_DIRECTIVES in parser based on context
        """

        from amplify.agent.objects.nginx.config import parser
        reload(parser)

    def setup_method(self, method):
        super(BaseControllerTestCase, self).setup_method(method)
        context.agent_name = 'controller'


class BaseConfiguratorTestCase(BaseControllerTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, tmpdir):
        self.tmpdir = tmpdir

    def setup_method(self, method):
        super(BaseConfiguratorTestCase, self).setup_method(method)
        from amplify.ext.configurator.config import ConfiguratorConfig
        self.original_config = copy.deepcopy(ConfiguratorConfig.config)
        context.app_config.add(ConfiguratorConfig())

    def teardown_method(self, method):
        from amplify.ext.configurator.config import ConfiguratorConfig
        ConfiguratorConfig.config = copy.deepcopy(self.original_config)
        context.app_config.remove(ConfiguratorConfig())
        super(BaseConfiguratorTestCase, self).teardown_method(method)


class WithConfigTestCase(BaseTestCase):

    def setup_method(self, method):
        super(WithConfigTestCase, self).setup_method(method)
        self.original_file = test.unit.agent.common.config.app.TestingConfig.filename
        self.fake_config_file = '%s.%s' % (self.original_file, self._testMethodName)
        test.unit.agent.common.config.app.TestingConfig.filename = self.fake_config_file

    def teardown_method(self, method):
        if os.path.exists(self.fake_config_file):
            os.remove(self.fake_config_file)
        test.unit.agent.common.config.app.TestingConfig.filename = self.original_file

    def mk_test_config(self, config=None):
        if os.path.exists(self.original_file):
            shutil.copyfile(self.original_file, self.fake_config_file)
        imp.reload(test.unit.agent.common.config.app)

        context.app_config = ConfigTank()
        context.app_config.add(test.unit.agent.common.config.app.TestingConfig())


class NginxCollectorTestCase(BaseTestCase):
    """
    Special class for collector tests
    Creates statsd stubd and object stub for collector envrionment
    """
    def setup_method(self, method):
        super(NginxCollectorTestCase, self).setup_method(method)

        class FakeNginxObject(AbstractObject):
            type = 'nginx'

            error_log_levels = (
                'debug',
                'info',
                'notice',
                'warn',
                'error',
                'crit',
                'alert',
                'emerg'
            )

        local_id = random.randint(1, 10000000)

        self.fake_object = FakeNginxObject(
            data={
                'bin_path': '/usr/sbin/nginx',
                'conf_path': '/etc/nginx/nginx.conf',
                'pid': '123',
                'local_id': local_id,
                'workers': []
            }
        )


class RealNginxTestCase(BaseTestCase):
    """
    Special class for tests on real nginx
    Launches nginx on setup and stops it on teardown

    All shell commands are called without check for 0 return code,
    since with nginx+ command service nginx start will return 1
    if nginx is already running
    """
    def setup_method(self, method):
        super(RealNginxTestCase, self).setup_method(method)
        self.running = False
        self.second_started = False
        self.start_first_nginx()
        self.running = True

    def teardown_method(self, method):
        if self.running:
            # use check=False because sometimes this returns code 123 on test-plus for some reason
            subp.call('pgrep nginx |sudo xargs kill -9', check=False)
            self.running = False
        super(RealNginxTestCase, self).teardown_method(method)

    def reload_nginx(self):
        subp.call('service nginx reload', check=False)
        time.sleep(0.5)

    def start_second_nginx(self, conf='nginx2.conf'):
        subp.call('/usr/sbin/nginx2 -c /etc/nginx/%s' % conf, check=False)
        self.second_started = True
        time.sleep(0.5)

    def stop_first_nginx(self):
        subp.call('service nginx stop', check=False)
        time.sleep(0.5)

    def start_first_nginx(self):
        subp.call('service nginx start', check=False)
        time.sleep(0.5)

    def restart_nginx(self):
        subp.call('service nginx restart', check=False)
        time.sleep(0.5)


class RealNginxSupervisordTestCase(RealNginxTestCase):

    @classmethod
    def setup_class(cls):
        subp.call('supervisorctl -c /etc/supervisord.conf shutdown', check=False)
        subp.call('supervisord -c /etc/supervisord.conf')

    @classmethod
    def teardown_class(cls):
        subp.call('supervisorctl -c /etc/supervisord.conf shutdown')

    def reload_nginx(self):
        subp.call('supervisorctl -c /etc/supervisord.conf signal HUP nginx')
        time.sleep(0.5)

    def start_second_nginx(self, conf='nginx2.conf'):
        subp.call('/usr/sbin/nginx2 -c /etc/nginx/%s' % conf)
        self.second_started = True
        time.sleep(0.5)

    def stop_first_nginx(self):
        subp.call('supervisorctl -c /etc/supervisord.conf stop nginx')
        time.sleep(0.5)

    def start_first_nginx(self):
        subp.call('supervisorctl -c /etc/supervisord.conf start nginx')
        time.sleep(0.5)

    def restart_nginx(self):
        subp.call('supervisorctl -c /etc/supervisord.conf restart nginx')
        time.sleep(0.5)


class TestWithFakeSubpCall(BaseTestCase):
    """
    Special class for testing functions whose output is dependent on subp.call
    This allows us to push the desired result of the next supb.call, that's returned when subp is called
    After the pushed results are all popped, subp.call will actually spin up a subprocess like usual
    """
    def push_subp_result(self, stdout_lines=None, stderr_lines=None, returncode=0):
        stdout_lines = [''] if stdout_lines is None else stdout_lines
        stderr_lines = [''] if stderr_lines is None else stderr_lines

        from amplify.agent.common.util import subp
        original_call = subp.call

        def fake_call(command, check=True):
            subp.call = original_call
            if check and returncode != 0:
                payload = {'returncode': returncode, 'error': '\n'.join(stderr_lines)}
                raise AmplifySubprocessError(message=command, payload=payload)
            return stdout_lines, stderr_lines

        subp.call = fake_call


def nginx_plus_installed():
    first_line = ''
    try:
        out, err = subp.call('/usr/sbin/nginx -V')
        first_line = err[0]
    except:
        pass
    return True if 'nginx-plus' in first_line else False


def nginx_installed():
    try:
        subp.call('/usr/sbin/nginx -V')
        return True
    except:
        return False


nginx_plus_test = pytest.mark.skipif(not nginx_plus_installed(), reason='This is a test for nginx+')
nginx_oss_test = pytest.mark.skipif(nginx_plus_installed(), reason='This is a test for OSS nginx')
nginx_test = pytest.mark.skipif(not nginx_installed(), reason='This is a test for OSS nginx')
plain_test = pytest.mark.skipif(nginx_installed(), reason='This is a test for plain OS system')
future_test = pytest.mark.skipif(1 > 0, reason='This test will be written in future')
disabled_test = pytest.mark.skipif(1 > 0, reason='This test has unexpected behavior')


def container_test(f):
    """
    Decorator that makes collectors think they're running inside docker
    """
    if host.os_name() == 'freebsd':
        return pytest.mark.skip(reason='FreeBSD cannot run in linux containers')

    def wrapper(*args, **kwargs):
        context.app_config['credentials']['imagename'] = 'DockerTest'
        f(*args, **kwargs)
        context.app_config['credentials']['imagename'] = None

    return wrapper
