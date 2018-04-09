# -*- coding: utf-8 -*-
from test.unit.agent.managers.status import StatusManagerTestCase

from amplify.agent.managers.api import ApiManager


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class ApiManagerTestCase(StatusManagerTestCase):
    plus_manager = ApiManager
    api = True
    collector_method = 'plus_api'
