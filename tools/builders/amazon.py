# -*- coding: utf-8 -*-
import os
import traceback

from util import shell_call, get_version_and_build, install_pip, install_pip_deps

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


def build(package=None):
    """
    Builds a rpm package for amazon linux

    :param package: str full package name
    """
    rpm_topdir = os.path.expanduser('~') + '/rpmbuild'
    rpm_sources = rpm_topdir + '/SOURCES'
    python = '/usr/bin/python2.7'

    # get version and build
    version, bld = get_version_and_build()

    # get arch
    arch = shell_call('uname -m').split('\n')[0]

    # install pip
    install_pip(python=python)

    try:
        # delete previous build
        shell_call('rm -rf %s' % rpm_sources)

        # create default rpmbuild dir
        try:
            os.makedirs(rpm_sources)
        except:
            pass

        # create a weird setup file (just like with any other rpm)
        if arch.endswith('_64'):
            """
            [install]
            install-purelib=$base/lib64/python
            """
            shell_call("echo '[install]' > setup.cfg")
            shell_call("echo 'install-purelib=$base/lib64/python' >> setup.cfg")

        # install all dependencies
        install_pip_deps(package=package)

        # remove weird file
        shell_call('rm -rf setup.cfg', important=False)

        # provide a new one - to create a package that will work with the strange amazon linux rpm
        shell_call("echo '[install]' > setup.cfg")
        shell_call("echo 'install_lib = /usr/lib/python2.7/dist-packages' >> setup.cfg")

        # create python package
        shell_call('cp packages/%s/setup.py ./' % package)
        shell_call('%s setup.py sdist --formats=gztar' % python)

        # copy gz file to rpmbuild/SOURCES/
        shell_call('cp -r dist/*.gz %s/' % rpm_sources)

        # create rpm package
        shell_call(
            'rpmbuild -D "_topdir %s" -bb packages/%s/rpm/%s.spec --define "amplify_version %s" --define "amplify_release %s"' % (
                rpm_topdir, package, package, version, bld
            )
        )

        # clean
        shell_call('rm -r dist', important=False)
        shell_call('rm -r *.egg-*', important=False)
        shell_call('rm -rf setup.cfg', important=False)
        shell_call('rm setup.py', important=False)
    except:
        print(traceback.format_exc())

