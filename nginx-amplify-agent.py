#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import platform

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"
__credits__ = []  # check amplify/agent/main.py for the actual credits list


# Detect old Centos6 before we do anything else
distname, distversion, __ = platform.linux_distribution(full_distribution_name=False)
is_centos_6 = distname.lower() == 'centos' and distversion.split('.')[0] == '6'
is_redhat_6 = distname.lower() == 'redhat' and distversion.split('.')[0] == '6'

# Import amplify python package and add it's path to sys path
# This needs to be done in order to load all requirements from amplify python package
import amplify
amplify_path = '/'.join(amplify.__file__.split('/')[:-1])
sys.path.insert(0, amplify_path)


# Import gevent and make appropriate patches (depends on platform)
from gevent import monkey
if is_centos_6 or is_redhat_6:
    monkey.patch_all(socket=False, ssl=False, select=False)
else:
    monkey.patch_all()


# Run the main script
from amplify.agent import main
main.run('amplify')
