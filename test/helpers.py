# -*- coding: utf-8 -*-
from functools import wraps

from hamcrest import *
from hamcrest.core.helpers.wrap_matcher import wrap_matcher

from amplify.agent.objects.abstract import AbstractObject

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class DummyObject(AbstractObject):
    """
    Dummy object to be used in unit tests of which require/use objects.
    """
    type = 'dummy'


class DummyRootObject(DummyObject):
    type = 'system'


class DummyNginxObject(DummyObject):
    type = 'nginx'


def collected_metric(matcher=None):
    matcher = anything() if matcher is None else wrap_matcher(matcher)
    return only_contains(contains(greater_than(1476820876), matcher))


def count_calls(func):
    @wraps(func)
    def _wrapped(*args, **kwargs):
        _wrapped.call_count += 1
        return func(*args, **kwargs)
    _wrapped.call_count = 0
    return _wrapped
