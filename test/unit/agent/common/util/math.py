# -*- coding: utf-8 -*-

from amplify.agent.common.util.math import median
from unittest import TestCase
from hamcrest import *

__author__ = "Raymond Lau"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Raymond Lau"
__email__ = "raymond.lau@nginx.com"


class MathTestCase(TestCase):

    def test_median(self):

        # even length
        assert_that(median([1, 3, 5, 7]), equal_to(4.0))
        # unsorted
        assert_that(median([1, 5, 7, 3]), equal_to(4.0))
        # odd length
        assert_that(median([1, 2, 3, 4, 5, 6, 7]), equal_to(4.0))
        assert_that(median([]), equal_to(None))
