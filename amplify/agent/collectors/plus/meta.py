# -*- coding: utf-8 -*-
from amplify.agent.common.context import context
from amplify.agent.collectors.abstract import AbstractMetaCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusObjectMetaCollector(AbstractMetaCollector):
    short_name = 'plus_meta'

    def __init__(self, **kwargs):
        super(PlusObjectMetaCollector, self).__init__(**kwargs)
        self.register(
            self.version
        )

    @property
    def default_meta(self):
        zone = self.object.type if self.object.type != 'server_zone' else 'status_zone'
        meta = {
            'type': self.object.type_template % zone,
            'local_name': self.object.local_name,
            'local_id': self.object.local_id,
            'root_uuid': context.uuid,
            'hostname': context.app_config['credentials']['imagename'] or context.hostname,
            'version': None
        }
        return meta

    def version(self):
        parent = context.objects.find_parent(obj=self.object)
        self.meta['version'] = parent.version if parent else None
