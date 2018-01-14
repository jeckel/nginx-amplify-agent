# -*- coding: utf-8 -*-
from hamcrest import (
    assert_that, equal_to, not_none, has_length
)

from test.base import BaseTestCase
from test.fixtures.defaults import DEFAULT_UUID
from amplify.ext.phpfpm.objects.master import PHPFPMObject


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMObjectTestCase(BaseTestCase):
    """
    Test case for PHPFPMObject (master).
    """

    def test_init(self):
        phpfpm_obj = PHPFPMObject(
            local_id=123,
            pid=2,
            cmd='php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
            conf_path='/etc/php5/fpm/php-fpm.conf',
            workers=[3, 4]
        )
        assert_that(phpfpm_obj, not_none())

        assert_that(phpfpm_obj.local_id_args, equal_to(
            ('php-fpm: master process (/etc/php5/fpm/php-fpm.conf)', '/etc/php5/fpm/php-fpm.conf')
        ))
        assert_that(phpfpm_obj.local_id, equal_to(123))
        assert_that(phpfpm_obj.definition, equal_to(
            {'local_id': 123, 'type': 'phpfpm', 'root_uuid': DEFAULT_UUID}
        ))
        assert_that(phpfpm_obj.definition_hash, equal_to(
            '32e8faf1747e8fa5778388b2db268941abeba7140cd83c52712ef97eb571e6d2'
        ))
        assert_that(phpfpm_obj.collectors, has_length(2))

    def test_parse(self):
        """This test is only possible because there is a working config in the test container"""
        phpfpm_obj = PHPFPMObject(
            local_id=123,
            pid=2,
            cmd='php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
            conf_path='/etc/php5/fpm/php-fpm.conf',
            workers=[3, 4]
        )
        assert_that(phpfpm_obj, not_none())

        parsed_conf = phpfpm_obj.parse()
        assert_that(parsed_conf, not_none())
        assert_that(parsed_conf, equal_to(
            {
                'pools': [
                    {
                        'status_path': '/status',
                        'name': 'www',
                        'file': '/etc/php5/fpm/pool.d/www.conf',
                        'listen': '/run/php/php7.0-fpm.sock'
                    },
                    {
                        'status_path': '/status',
                        'name': 'www2',
                        'file': '/etc/php5/fpm/pool.d/www2.conf',
                        'listen': '127.0.0.1:51'
                    }
                ],
                'include': ['/etc/php5/fpm/pool.d/*.conf'],
                'file': '/etc/php5/fpm/php-fpm.conf'
            }
        ))

    def test_properties(self):
        """
        This test is meant to test some properties that have had intermittent
        user bug reports.
        """
        phpfpm_obj = PHPFPMObject(
            pid=2,
            cmd='php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
            conf_path='/etc/php5/fpm/php-fpm.conf',
            workers=[3, 4]
        )
        assert_that(phpfpm_obj, not_none())

        assert_that(phpfpm_obj.local_id_args, equal_to(
            (
                'php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
                '/etc/php5/fpm/php-fpm.conf'
            )
        ))
        assert_that(phpfpm_obj.local_id, equal_to(
            'e5942daaa5bf35af722bac3b9582b17c07515f0f77936fb5c7f771c7736cc157'
        ))
        assert_that(phpfpm_obj.definition, equal_to(
            {
                'local_id': 'e5942daaa5bf35af722bac3b9582b17c07515f0f77936fb5c7f771c7736cc157',
                'type': 'phpfpm',
                'root_uuid': DEFAULT_UUID
            }
        ))
        assert_that(phpfpm_obj.definition_hash, equal_to(
            '6ee51f6b649782e5dd04db052e7a018372645756378a7a3de3356c2ae6ff3bd7'
        ))
