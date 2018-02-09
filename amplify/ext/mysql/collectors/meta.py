# -*- coding: utf-8 -*-
from amplify.agent.collectors.abstract import AbstractMetaCollector
from amplify.agent.common.context import context
from amplify.agent.common.util import subp, host
from amplify.ext.mysql.util import LS_CMD, LS_CMD_FREEBSD, ls_parser, version_parser

__author__ = "Andrew Alexeev"
__copyright__ = "Copyright (C) Nginx Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class MySQLMetaCollector(AbstractMetaCollector):

    short_name = 'mysql_meta'

    def __init__(self, **kwargs):
        super(MySQLMetaCollector, self).__init__(**kwargs)

        self._bin_path = None  # cache for bin_path discovery
        self._version = None  # cache for version discovery
        self._version_line = None  # "" "" ""

        self.register(
            self.bin_path,
            self.version
        )

    @property
    def default_meta(self):
        meta = {
            'type': self.object.type,
            'root_uuid': context.uuid,
            'local_id': self.object.local_id,
            'name': self.object.name,
            'display_name': self.object.display_name,
            'cmd': self.object.cmd,
            'conf_path': self.object.conf_path,
            'bin_path': None,
            'version': None,
            'version_line': None,
            'can_have_children': False
        }

        if not self.in_container:
            meta['pid'] = self.object.pid

        return meta

    def bin_path(self):
        """
        Finds and sets as a var the path to the running binary of the mysql server
        """
        if '/' in self.object.cmd:
            self._bin_path = self.object.cmd.split(' ')[0]

        if self._bin_path is None:
            ls_cmd_template = LS_CMD_FREEBSD if host.linux_name() == 'freebsd' else LS_CMD
            ls_cmd = ls_cmd_template % self.object.pid

            try:
                ls, _ = subp.call(ls_cmd, check=False)
                context.log.debug('ls "%s" output: %s' % (ls_cmd, ls))
            except Exception as e:
                exc_name = e.__class__.__name__

                # this is being kept as an error because it has
                # implications for meta collection success/failure
                context.log.debug(
                    'failed to find MySQL bin path: "%s" failed due to %s' %
                    (ls_cmd, exc_name)
                )
                context.log.debug('additional info:', exc_info=True)
            else:
                try:
                    self._bin_path = ls_parser(ls[0])
                except Exception as e:
                    exc_name = e.__class__.__name__
                    context.log.debug(
                        'failed to parse ls result "%s" due to %s' %
                        (ls[0], exc_name)
                    )
                    context.log.debug('additional info:', exc_info=True)

        self.meta['bin_path'] = self._bin_path

    def version(self):
        """
        Finds and sets version
        """
        # only compute if version hasn't been found before and we have found a bin_path
        if self._version is None and self.object.cmd is not None:
            version, raw_line = version_parser(self.object.cmd)
            self._version, self._version_line = version, raw_line

        self.meta['version'] = self._version
        self.meta['version_line'] = self._version_line
