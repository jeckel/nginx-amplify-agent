# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.ext.abstract.object import AbstractExtObject
from test.fixtures.defaults import DEFAULT_UUID
from test.base import BaseTestCase


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class AbstractObjectTestCase(BaseTestCase):
    def test_basic(self):
        abstract_obj = AbstractExtObject()

        # Test things only different from standard abstract object (amplify.agent.objects.abstract)
        assert_that(abstract_obj, not_(equal_to(None)))
        assert_that(abstract_obj.definition, equal_to({
            'type': 'abstract',
            'local_id': None,
            'root_uuid': DEFAULT_UUID
        }))
        assert_that(abstract_obj.name, equal_to(None))
        assert_that(abstract_obj.display_name, equal_to('abstract @ hostname.nginx'))
