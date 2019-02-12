# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase
from test.unit.agent.common.config.app import TestingConfig

from amplify.agent.tanks.config import ConfigTank


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class ConfigTankTestCase(BaseTestCase):
    def setup_method(self, method):
        super(ConfigTankTestCase, self).setup_method(method)
        self.config_tank = ConfigTank()

    def teardown_method(self, method):
        self.config_tank = None
        super(ConfigTankTestCase, self).teardown_method(method)

    def test_add(self):
        config = TestingConfig()

        self.config_tank.add(config)

        assert_that(self.config_tank._configs, has_length(1))

        # check path index
        assert_that(self.config_tank._path_index, has_length(1))
        assert_that(self.config_tank._path_index, has_item(config.filename))

        # check name index
        assert_that(self.config_tank._name_index, has_length(1))
        assert_that(self.config_tank._name_index, has_item('agent.conf.testing'))

        # check section index
        assert_that(self.config_tank._section_index, has_length(greater_than(0)))
        assert_that(self.config_tank._section_index, has_item('daemon'))
        assert_that(self.config_tank._section_index, has_item('cloud'))
        assert_that(self.config_tank._section_index, has_item('credentials'))
        assert_that(self.config_tank._section_index, has_item('containers'))

    def test_load(self):
        self.config_tank.load(TestingConfig.filename)
        assert_that(self.config_tank._configs, has_length(1))

        # check path index
        assert_that(self.config_tank._path_index, has_length(1))
        assert_that(self.config_tank._path_index, has_item(TestingConfig.filename))

        # check name index
        assert_that(self.config_tank._name_index, has_length(1))
        assert_that(self.config_tank._name_index, has_item('agent.conf.testing'))

        # check section index
        assert_that(self.config_tank._section_index, has_length(greater_than(0)))
        # file doesn't have daemon
        assert_that(self.config_tank._section_index, has_item('cloud'))
        assert_that(self.config_tank._section_index, has_item('credentials'))
        # file doesn't have containers

    def test_get_config(self):
        config = TestingConfig()

        self.config_tank.add(config)
        assert_that(self.config_tank._configs, has_length(1))

        returned_config = self.config_tank.get_config('etc/agent.conf.testing')
        assert_that(id(returned_config), equal_to(id(config)))
