#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys

from builders import deb, rpm, amazon
from builders.util import shell_call

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


if __name__ == '__main__':
    package = 'nginx-amplify-agent' if len(sys.argv) == 1 else sys.argv[1]

    if os.path.isfile('/etc/debian_version'):
        deb.build(package=package)
    elif os.path.isfile('/etc/redhat-release'):
        rpm.build(package=package)
    else:
        os_release = shell_call('cat /etc/os-release', important=False)

        if 'amazon linux ami' in os_release.lower():
            amazon.build(package=package)
        else:
            print("sorry, it will be done later\n")
