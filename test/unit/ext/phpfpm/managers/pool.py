# -*- coding: utf-8 -*-
from hamcrest import *
import time

from test.unit.ext.phpfpm.base import PHPFPMTestCase, PHPFPMSupervisordTestCase
from amplify.agent.common.context import context

from amplify.ext.phpfpm.managers.master import PHPFPMManager
from amplify.ext.phpfpm.managers.pool import PHPFPMPoolManager


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMPoolManagerTestCase(PHPFPMTestCase):
    """
    Test case for PHPFPMPoolManager.
    """

    def setup_method(self, method):
        super(PHPFPMPoolManagerTestCase, self).setup_method(method)
        context._setup_object_tank()
        self.phpfpm_manager = PHPFPMManager()
        self.phpfpm_manager._discover_objects()

    def teardown_method(self, method):
        context._setup_object_tank()
        super(PHPFPMPoolManagerTestCase, self).teardown_method(method)

    def test_find_all(self):
        pool_manager = PHPFPMPoolManager()
        assert_that(pool_manager, not_none())

        found_pools = pool_manager._find_all()
        assert_that(found_pools, not_none())
        assert_that(found_pools, has_length(2))

        # This checks the first pool in the found_pools and makes assumptions
        # as to which one it will be.  This may not be true on other test
        # systems
        found_pool = found_pools[0]
        assert_that(found_pool['parent_id'], equal_to(1))
        assert_that(found_pool['parent_local_id'], equal_to(
            'e5942daaa5bf35af722bac3b9582b17c07515f0f77936fb5c7f771c7736cc157'
        ))
        assert_that(found_pool['local_id'], equal_to(
            '6eea242cd7825e81d309458c302b8bd18923812eb99ae70f2e8b5c5fb18d02b3'
        ))
        assert_that(found_pool['file'], equal_to('/etc/php5/fpm/pool.d/www.conf'))
        assert_that(found_pool['name'], equal_to('www'))
        assert_that(found_pool['listen'], equal_to('/run/php/php7.0-fpm.sock'))
        assert_that(found_pool['status_path'], equal_to('/status'))

    def test_discover_objects(self):
        pool_manager = PHPFPMPoolManager()
        assert_that(pool_manager, not_none())

        # check to make sure there are no pools
        current_pools = context.objects.find_all(types=pool_manager.types)
        assert_that(current_pools, has_length(0))

        # find pools
        pool_manager._discover_objects()

        # check that a pool is found
        current_pools = context.objects.find_all(types=pool_manager.types)
        assert_that(current_pools, has_length(2))

    def test_remove(self):
        pool_manager = PHPFPMPoolManager()
        assert_that(pool_manager, not_none())

        # check to make sure there are no pools
        current_pools = context.objects.find_all(types=pool_manager.types)
        assert_that(current_pools, has_length(0))

        # find pools
        pool_manager._discover_objects()

        # check that a pool is found
        current_pools = context.objects.find_all(types=pool_manager.types)
        assert_that(current_pools, has_length(2))

        # stop php-fpm
        self.stop_fpm()

        time.sleep(0.1)  # release gil

        # re-run master manager to remove the master
        self.phpfpm_manager._discover_objects()

        # check to see pools are also removed
        current_pools = context.objects.find_all(types=pool_manager.types)
        assert_that(current_pools, has_length(0))


class SupervisorPHPFPMPoolManagerTestCase(PHPFPMPoolManagerTestCase, PHPFPMSupervisordTestCase):
    pass
