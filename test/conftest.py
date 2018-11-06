# -*- coding: utf-8 -*-
import pytest

from amplify.agent.common.context import context

__author__ = "Arie van Luttikhuizen"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Arie van Luttikhuizen"
__email__ = "arie@nginx.com"


@pytest.fixture()
def docker():
    """
    Use this fixture to test how the agent will act in a Docker container.
    """
    context.app_config['credentials']['imagename'] = 'DockerTest'
    yield
    context.app_config['credentials']['imagename'] = None
