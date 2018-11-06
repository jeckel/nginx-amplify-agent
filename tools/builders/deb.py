# -*- coding: utf-8 -*-
import os
import traceback

from util import shell_call, get_version_and_build, change_first_line, install_pip, install_pip_deps

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


def build(package=None):
    """
    Builds a deb package

    :param package: str full package name
    """
    pkg_root = os.path.expanduser('~') + '/agent-pkg-root'
    pkg_final = os.path.expanduser('~') + '/agent-package'

    # get version and build
    version, bld = get_version_and_build()

    # get codename
    codename = shell_call("lsb_release -cs").rstrip('\n')

    # install pip
    install_pip()

    try:
        # delete previous build
        shell_call('rm -rf %s' % pkg_root)
        shell_call('rm -rf %s && mkdir %s' % (pkg_final, pkg_final))

        # install all dependencies
        install_pip_deps(package=package)

        # create python package
        shell_call('cp packages/%s/setup.py ./' % package)
        shell_call('python setup.py install --install-layout=deb --prefix=/usr --root=%s/%s-%s/debian/%s' % (pkg_root, package, version, package))

        # copy debian files to pkg-root
        shell_call('cp -r packages/%s/deb/debian %s/%s-%s/' % (package, pkg_root, package, version))

        # sed first line of changelog
        changelog_first_line = '%s (%s-%s~%s) %s; urgency=low' % (package, version, bld, codename, codename)
        change_first_line('%s/%s-%s/debian/changelog' % (pkg_root, package, version), changelog_first_line)

        # create deb package
        shell_call('cd %s/%s-%s && debuild -us -uc' % (pkg_root, package, version), terminal=True)
        shell_call('cp %s/*.deb %s/' % (pkg_root, pkg_final))

        # clean
        shell_call('rm -r build', important=False)
        shell_call('rm -r *.egg-*', important=False)
        shell_call('rm setup.py', important=False)
    except:
        print(traceback.format_exc())
