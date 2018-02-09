# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.common.util import ssl
from test.base import BaseTestCase

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class SSLAnalysisTestCase(BaseTestCase):

    def test_issuer_with_apostrophe(self):
        """
        Old regex method test.
        """
        result = {}
        line = "issuer= /C=US/O=Let's Encrypt/CN=Let's Encrypt Authority X1"

        for regex in ssl.ssl_regexs:
            match_obj = regex.match(line)
            if match_obj:
                result.update(match_obj.groupdict())

        assert_that(result, has_key('organization'))
        assert_that(result['organization'], equal_to("Let's Encrypt"))
        assert_that(result, has_key('common_name'))
        assert_that(result['common_name'], equal_to("Let's Encrypt Authority X1"))

    def test_structured_parse(self):
        lines = ["subject= CN=another.domain.com,OU=Domain Control Validated"]
        result = ssl.parse_raw_certificate_subject(lines)

        assert_that(result, has_key('common_name'))
        assert_that(result['common_name'], equal_to('another.domain.com'))
        assert_that(result, has_key('unit'))
        assert_that(result['unit'], equal_to('Domain Control Validated'))

    def test_complicated_common_name(self):
        lines = ["Subject: C=RU, ST=SPb, L=SPb, O=Fake Org, OU=D, CN=*.fake.domain.ru/emailAddress=fake@email.cc"]
        result = ssl.parse_raw_certificate_subject(lines)

        assert_that(result, has_length(6))

        assert_that(result, has_key('common_name'))
        assert_that(result['common_name'], equal_to('*.fake.domain.ru/emailAddress=fake@email.cc'))
        assert_that(result, has_key('unit'))
        assert_that(result['unit'], equal_to('D'))
        assert_that(result, has_key('organization'))
        assert_that(result['organization'], equal_to('Fake Org'))

    def test_international_common_name(self):
        results = ssl.certificate_subject("test/fixtures/nginx/ssl/idn/idn_cert.pem")
        assert_that(results['common_name'], equal_to('АБВГҐ.あいうえお'))
        assert_that(results['organization'], equal_to('АҐДЂ我要شث'))
        assert_that(results['state'], equal_to('FakeState'))
        assert_that(results['country'], equal_to('RU'))
        assert_that(results['unit'], equal_to('IT'))
