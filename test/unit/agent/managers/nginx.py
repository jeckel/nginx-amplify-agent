# -*- coding: utf-8 -*-
import re
import copy

from time import sleep
from hamcrest import *

from amplify.agent.common.util import subp
from amplify.agent.common.context import context
from amplify.agent.managers.nginx import NginxManager
from test.base import RealNginxTestCase, container_test, RealNginxSupervisordTestCase
from test.helpers import DummyRootObject

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class NginxManagerTestCase(RealNginxTestCase):
    def get_master_workers(self):
        master, workers = None, []
        ps, _ = subp.call('ps -xa -o pid,ppid,command | egrep "PID|nginx" | grep -v egrep')
        for line in ps:
            # 21355     1 nginx: master process /usr/sbin/nginx
            gwe = re.match(r'\s*(?P<pid>\d+)\s+(?P<ppid>\d+)\s+(?P<cmd>.+)\s*', line)

            # if not parsed - switch to next line
            if not gwe or 'py.test' in line:
                continue

            pid = int(gwe.group('pid'))
            cmd = gwe.group('cmd')

            if 'nginx: master process' in cmd:
                master = pid
            else:
                workers.append(pid)
        return master, workers

    def test_find_all(self):
        manager = NginxManager()
        nginxes = manager._find_all()
        assert_that(nginxes, has_length(1))

        definition, data = nginxes.pop(0)
        assert_that(data, has_key('pid'))
        assert_that(data, has_key('workers'))

        # get ps info
        master, workers = self.get_master_workers()

        assert_that(master, equal_to(data['pid']))
        assert_that(workers, equal_to(data['workers']))

    def test_restart(self):
        old_master, old_workers = self.get_master_workers()

        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.find_all(types=manager.types), has_length(1))
        obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))

        self.restart_nginx()
        new_master, new_workers = self.get_master_workers()

        manager._discover_objects()
        assert_that(manager.objects.find_all(types=manager.types), has_length(1))
        obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(obj.pid, not_(equal_to(old_master)))
        assert_that(obj.pid, equal_to(new_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))

    def test_reload(self):
        old_master, old_workers = self.get_master_workers()

        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.find_all(types=manager.types), has_length(1))
        obj = manager.objects.find_all(types=manager.types)[0]

        # The following assertion is unreliable for some reason.
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))

        self.reload_nginx()
        sleep(1)  # nginx needs some time to reload

        new_master, new_workers = self.get_master_workers()
        assert_that(new_master, equal_to(old_master))

        manager._discover_objects()
        obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))

    def test_two_instances(self):
        manager = NginxManager()
        manager._discover_objects()
        obj = manager.objects.find_all(types=manager.types)[0]

        self.start_second_nginx()

        manager._discover_objects()
        assert_that(manager.objects.find_all(types=manager.types), has_length(2))

        local_ids = map(lambda x: x.local_id, manager.objects.find_all(types=manager.types))
        assert_that(local_ids, has_item(obj.local_id))

    def test_find_none(self):
        # Kill running NGINX so that it finds None
        subp.call('pgrep nginx |sudo xargs kill -9', check=False)
        self.running = False

        # Setup dummy object
        context.objects.register(DummyRootObject())

        manager = NginxManager()
        nginxes = manager._find_all()
        assert_that(nginxes, has_length(0))

        root_object = context.objects.root_object
        assert_that(root_object.eventd.current, has_length(1))

        # Reset objects...
        context.objects = None
        context._setup_object_tank()


@container_test
class DockerNginxManagerTestCase(NginxManagerTestCase):

    def test_restart(self):
        old_master, old_workers = self.get_master_workers()

        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.find_all(types=manager.types), has_length(1))
        obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))
        assert_that(obj.type, equal_to('container_nginx'))

        self.restart_nginx()
        new_master, new_workers = self.get_master_workers()

        manager._discover_objects()
        assert_that(manager.objects.find_all(types=manager.types), has_length(1))
        obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(obj.pid, not_(equal_to(old_master)))
        assert_that(obj.pid, equal_to(new_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))
        assert_that(obj.type, equal_to('container_nginx'))

    def test_reload(self):
        old_master, old_workers = self.get_master_workers()

        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.find_all(types=manager.types), has_length(1))
        obj = manager.objects.find_all(types=manager.types)[0]
        # The following assertion is unreliable for some reason.
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))
        assert_that(obj.type, equal_to('container_nginx'))

        self.reload_nginx()
        sleep(1)  # nginx needs some time to reload

        new_master, new_workers = self.get_master_workers()
        assert_that(new_master, equal_to(old_master))

        manager._discover_objects()
        obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))
        assert_that(obj.type, equal_to('container_nginx'))

    def test_two_instances(self):
        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.find_all(types=manager.types), has_length(1))
        obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(obj.type, equal_to('container_nginx'))

        self.start_second_nginx()

        manager._discover_objects()
        assert_that(manager.objects.find_all(types=manager.types), has_length(2))

        local_ids = map(lambda x: x.local_id, manager.objects.find_all(types=manager.types))
        assert_that(local_ids, has_item(obj.local_id))


class SupervisorNginxManagerTestCase(NginxManagerTestCase, RealNginxSupervisordTestCase):
    pass
