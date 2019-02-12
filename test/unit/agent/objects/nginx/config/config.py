# -*- coding: utf-8 -*-
import os

from hamcrest import *

from amplify.agent.common.context import context
from amplify.agent.managers.nginx import NginxManager
from amplify.agent.objects.nginx.config.config import ERROR_LOG_LEVELS, NginxConfig
from test.base import BaseTestCase, RealNginxTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"

simple_config = os.getcwd() + '/test/fixtures/nginx/simple/nginx.conf'
complex_config = os.getcwd() + '/test/fixtures/nginx/complex/nginx.conf'
huge_config = os.getcwd() + '/test/fixtures/nginx/huge/nginx.conf'
broken_config = os.getcwd() + '/test/fixtures/nginx/broken/nginx.conf'
proxy_buffers_simple_config = os.getcwd() + '/test/fixtures/nginx/proxy_buffers_simple/nginx.conf'
proxy_buffers_complex_config = os.getcwd() + '/test/fixtures/nginx/proxy_buffers_complex/nginx.conf'
tabs_config = os.getcwd() + '/test/fixtures/nginx/custom/tabs.conf'
fastcgi_config = os.getcwd() + '/test/fixtures/nginx/fastcgi/nginx.conf'
json_config = os.getcwd() + '/test/fixtures/nginx/custom/json.conf'
ssl_simple_config = os.getcwd() + '/test/fixtures/nginx/ssl/simple/nginx.conf'
regex_status_config = os.getcwd() + '/test/fixtures/nginx/regex_status/nginx.conf'
wildcard_directory_config = os.getcwd() + '/test/fixtures/nginx/wildcard_directory/etc/nginx/nginx.conf'
tabs_everywhere = os.getcwd() + '/test/fixtures/nginx/tabs/nginx.conf'
status_urls = os.getcwd() + '/test/fixtures/nginx/status_urls/nginx.conf'
log_format_string_concat = os.getcwd() + '/test/fixtures/nginx/custom/log_format_string_concat.conf'
log_format_unicode_quote = os.getcwd() + '/test/fixtures/nginx/custom/log_format_unicode_quote.conf'
log_format_escaped_json = os.getcwd() + '/test/fixtures/nginx/custom/log_format_escaped_json.conf'
bad_log_directives_config = os.getcwd() + '/test/fixtures/nginx/broken/bad_logs.conf'


class ConfigLogsTestCase(RealNginxTestCase):

    def test_logs_path(self):
        self.stop_first_nginx()
        self.start_second_nginx(conf='nginx_no_logs.conf')
        manager = NginxManager()
        manager._discover_objects()
        assert_that(manager.objects.objects_by_type[manager.type], has_length(1))
        # get nginx object
        nginx_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]
        assert_that(nginx_obj.config.access_logs, has_length(1))
        assert_that(nginx_obj.config.access_logs, has_key('/var/log/nginx/access.log'))
        assert_that(nginx_obj.config.error_logs, has_length(1))
        assert_that(nginx_obj.config.error_logs, has_key('/var/log/nginx/error.log'))


class ConfigTestCase(BaseTestCase):

    def test_parse_simple(self):
        config = NginxConfig(simple_config)
        config.full_parse()

        # error logs
        assert_that(config.error_logs, has_length(1))
        assert_that(config.error_logs, has_key('/var/log/nginx/error.log'))
        assert_that(config.error_logs.values(), only_contains(
            has_entries(
                log_level=is_in(ERROR_LOG_LEVELS),
                permissions=matches_regexp('[0-7]{4}'),
                readable=instance_of(bool)
            )
        ))

        # access logs
        assert_that(config.access_logs, has_length(2))
        assert_that(config.access_logs, has_item('/var/log/nginx/access.log'))
        assert_that(config.access_logs, has_item('/var/log/nginx/superaccess.log'))
        assert_that(config.access_logs['/var/log/nginx/access.log']['log_format'], equal_to('super_log_format'))
        assert_that(config.access_logs.values(), only_contains(
            has_entries(
                log_format=any_of(is_in(config.log_formats), none()),
                permissions=matches_regexp('[0-7]{4}'),
                readable=instance_of(bool)
            )
        ))

        # log formats
        assert_that(config.log_formats, has_length(1))
        assert_that(config.log_formats, has_item('super_log_format'))
        assert_that(
            config.log_formats['super_log_format'],
            equal_to(
                '$remote_addr - $remote_user [$time_local] "$request" $status ' +
                '$body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" ' +
                'rt="$request_time" ua="$upstream_addr" us="$upstream_status" ' +
                'ut="$upstream_response_time" "$gzip_ratio"'
            )
        )

        # stub status urls
        assert_that(config.stub_status_urls, has_length(2))
        assert_that(config.stub_status_urls[0], equal_to('http://127.0.0.1:81/basic_status'))

        # status urls
        assert_that(config.plus_status_external_urls, has_length(2))
        assert_that(config.plus_status_external_urls, has_item('http://127.0.0.1:81/plus_status'))
        assert_that(config.plus_status_external_urls, has_item('https://127.0.0.1:443/plus_status'))

        assert_that(config.plus_status_internal_urls, has_length(2))
        assert_that(config.plus_status_internal_urls, has_item('http://127.0.0.1:81/plus_status'))

        # api urls
        assert_that(config.api_external_urls, has_length(2))
        assert_that(config.api_external_urls, has_item('http://127.0.0.1:81/api'))
        assert_that(config.api_external_urls, has_item('https://127.0.0.1:443/api'))

        assert_that(config.api_internal_urls, has_length(2))
        assert_that(config.api_internal_urls, has_item('http://127.0.0.1:81/api'))
        assert_that(config.api_external_urls, has_item('https://127.0.0.1:443/api'))

    def test_parse_huge(self):
        config = NginxConfig(huge_config)
        config.full_parse()

        # error logs
        assert_that(config.error_logs, has_length(1))
        assert_that(config.error_logs, has_key('/var/log/nginx-error.log'))
        assert_that(config.error_logs.values(), only_contains(
            has_entries(
                log_level=is_in(ERROR_LOG_LEVELS),
                permissions=matches_regexp('[0-7]{4}'),
                readable=instance_of(bool)
            )
        ))

        # access logs
        assert_that(config.access_logs, has_length(6))
        assert_that(config.access_logs, has_item('/var/log/default.log'))
        assert_that(config.access_logs, has_item('/var/log/pp.log'))
        assert_that(config.access_logs['/var/log/pp.log']['log_format'], equal_to('main'))
        assert_that(config.access_logs.values(), only_contains(
            any_of(
                has_entries(
                    log_format=any_of(is_in(config.log_formats), none()),
                    permissions=matches_regexp('[0-7]{4}'),
                    readable=instance_of(bool)
                ),
                all_of(
                    has_length(1),
                    has_entries(
                        log_format=any_of(is_in(config.log_formats), none())
                    )
                )  # syslog will not have permissions or readable values
            )
        ))

        # log formats
        assert_that(config.log_formats, has_length(1))
        assert_that(config.log_formats, has_item('main'))
        assert_that(
            config.log_formats['main'],
            equal_to(
                '$remote_addr - $remote_user [$time_local] "$request" ' +
                '$status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for"'
            )
        )

        # stub status url
        assert_that(config.stub_status_urls, has_length(2))
        assert_that(config.stub_status_urls[0], equal_to('http://127.0.0.1:80/nginx_status'))

    def test_parse_complex(self):
        config = NginxConfig(complex_config)
        config.full_parse()

        assert_that(config.error_logs, empty())
        assert_that(config.access_logs, empty())
        assert_that(config.log_formats, empty())
        assert_that(config.stub_status_urls, empty())

    def test_broken(self):
        config = NginxConfig(broken_config)
        config.full_parse()

        assert_that(config.tree, has_entries({
            'status': 'failed',
            'errors': has_length(2),
            'config': contains(
                has_entries({
                    'file': '/amplify/test/fixtures/nginx/broken/nginx.conf',
                    'status': 'failed',
                    'errors': contains(
                        has_entries({
                            'line': 9,
                            'error': '"http" directive is not allowed here in /amplify/test/fixtures/nginx/broken/nginx.conf:9'
                        }),
                        has_entries({
                            'line': 11,
                            'error': 'unexpected end of file, expecting "}" in /amplify/test/fixtures/nginx/broken/nginx.conf:11'
                        })
                    )
                })
            )
        }))

    def test_broken_includes(self):
        config = NginxConfig(huge_config)
        config.full_parse()

        assert_that(config.tree, has_entries({
            'status': 'failed',
            'errors': has_length(9),
            'config': contains(
                has_entries({
                    'file': '/amplify/test/fixtures/nginx/huge/nginx.conf',
                    'status': 'failed',
                    'errors': contains(
                        {'error': "[Errno 2] No such file or directory: '/amplify/test/fixtures/nginx/huge/mime.types2'", 'line': 13},
                        {'error': "[Errno 2] No such file or directory: '/amplify/test/fixtures/nginx/huge/dir.map'", 'line': 31},
                        {'error': "[Errno 2] No such file or directory: '/amplify/test/fixtures/nginx/huge/ec2-public-networks.conf'", 'line': 114},
                        {'error': "[Errno 2] No such file or directory: '/amplify/test/fixtures/nginx/huge/ec2-public-networks.conf'", 'line': 117},
                        {'error': "[Errno 2] No such file or directory: '/amplify/test/fixtures/nginx/huge/ec2-public-networks.conf'", 'line': 120},
                        {'error': "[Errno 2] No such file or directory: '/amplify/test/fixtures/nginx/huge/ec2-public-networks.conf'", 'line': 123},
                        {'error': "[Errno 2] No such file or directory: '/amplify/test/fixtures/nginx/huge/ec2-public-networks.conf'", 'line': 126},
                        {'error': "[Errno 2] No such file or directory: '/amplify/test/fixtures/nginx/huge/azure-public-networks.conf'", 'line': 129},
                        {'error': "[Errno 2] No such file or directory: '/amplify/test/fixtures/nginx/huge/gce-public-networks.conf'", 'line': 132},
                    )
                }),
                has_entries({
                    'file': '/amplify/test/fixtures/nginx/huge/mime.types',
                    'status': 'ok'
                })
            )
        }))

        # despite there being 8 errors, there are only 5 missing includes
        assert_that(config.parser_errors, has_length(5))

    def test_proxy_buffers_simple(self):
        config = NginxConfig(proxy_buffers_simple_config)
        config.full_parse()

        assert_that(config.subtree, has_item(
            has_entries({
                'directive': 'http',
                'block': has_items(
                    has_entries({'directive': 'proxy_buffering'}),
                    has_entries({'directive': 'proxy_buffers'})
                )
            })
        ))

        assert_that(config.parser_errors, empty())
        assert_that(config.test_errors, empty())

    def test_proxy_buffers_complex(self):
        config = NginxConfig(proxy_buffers_complex_config)
        config.full_parse()

        assert_that(config.subtree, has_item(
            has_entries({
                'directive': 'http',
                'block': has_items(
                    has_entries({'directive': 'proxy_buffering'}),
                    has_entries({'directive': 'proxy_buffers'}),
                    has_entries({
                        'directive': 'server',
                        'block': has_item(
                            has_entries({
                                'directive': 'location',
                                'args': ['/'],
                                'block': has_items(
                                    has_entries({'directive': 'proxy_pass'}),
                                    has_entries({'directive': 'proxy_buffering'}),
                                    has_entries({'directive': 'proxy_buffers'})
                                )
                            })
                        )
                    })
                )
            })
        ))

        assert_that(config.parser_errors, empty())
        assert_that(config.test_errors, empty())

    def test_parse_tabbed_config(self):
        config = NginxConfig(tabs_config)
        config.full_parse()

        # common structure
        assert_that(config.subtree, contains(
            has_entries({'directive': 'user'}),
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'error_log'}),
            has_entries({'directive': 'pid'}),
            has_entries({'directive': 'events'}),
            has_entries({'directive': 'http'})
        ))

        http = config.subtree[5]['block']
        assert_that(http, contains(
            has_entries({'directive': 'charset'}),
            has_entries({'directive': 'log_format'}),
            has_entries({'directive': 'access_log'}),
            has_entries({'directive': 'proxy_cache_path'}),
            has_entries({'directive': 'sendfile'}),
            has_entries({'directive': 'keepalive_timeout'}),
            has_entries({'directive': 'gzip'}),
            has_entries({'directive': 'gzip_types'}),
            has_entries({'directive': 'root'}),
            has_entries({'directive': 'server'}),
            has_entries({'directive': 'server'}),
            has_entries({'directive': 'upstream'}),
            has_entries({'directive': 'server'}),
            has_entries({'directive': 'server'}),
        ))

        log_format_args = http[1]['args']
        assert_that(log_format_args[0], equal_to('main'))
        assert_that(log_format_args[1], equal_to(
            '"$time_local"\\t"$remote_addr"\\t"$http_host"\\t"$request"\\t'
            '"$status"\\t"$body_bytes_sent\\t"$http_referer"\\t'
            '"$http_user_agent"\\t"$http_x_forwarded_for"'
        ))

        assert_that(
            config.log_formats['main'],
            equal_to(
                '"$time_local"\t"$remote_addr"\t"$http_host"\t"$request"\t'
                '"$status"\t"$body_bytes_sent\t"$http_referer"\t'
                '"$http_user_agent"\t"$http_x_forwarded_for"'
            )
        )

    def test_fastcgi(self):
        config = NginxConfig(fastcgi_config)
        config.full_parse()

        assert_that(config.subtree, contains(
            has_entries({'directive': 'user'}),
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'pid'}),
            has_entries({'directive': 'events'}),
            has_entries({
                'directive': 'http',
                'block': contains(
                    has_entries({'directive': 'sendfile'}),
                    has_entries({'directive': 'tcp_nopush'}),
                    has_entries({'directive': 'tcp_nodelay'}),
                    has_entries({'directive': 'keepalive_timeout'}),
                    has_entries({'directive': 'types_hash_max_size'}),
                    has_entries({'directive': 'include', 'args': ['mime.types']}),
                    has_entries({'directive': 'types'}),
                    has_entries({'directive': 'default_type'}),
                    has_entries({'directive': 'proxy_buffering'}),
                    has_entries({'directive': 'log_format'}),
                    has_entries({'directive': 'access_log'}),
                    has_entries({'directive': 'error_log'}),
                    has_entries({'directive': 'gzip'}),
                    has_entries({'directive': 'gzip_disable'}),
                    has_entries({'directive': 'include', 'args': ['conf.d/*.conf']}),
                    has_entries({
                        'directive': 'server',
                        'block': contains(
                            has_entries({'directive': 'listen'}),
                            has_entries({'directive': 'index'}),
                            has_entries({'directive': 'access_log'}),
                            has_entries({
                                'directive': 'location',
                                'block': contains(
                                    has_entries({'directive': 'include', 'args': ['fastcgi_params']}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_param'}),
                                    has_entries({'directive': 'fastcgi_pass'}),
                                )
                            }),
                        )
                    }),
                    has_entries({
                        'directive': 'server',
                        'block': has_length(5)
                    })
                )
            })
        ))

    def test_json(self):
        config = NginxConfig(json_config)
        config.full_parse()

        assert_that(config.log_formats, has_key('json'))
        assert_that(
            config.log_formats['json'],
            equal_to('{ "time_iso8601": "$time_iso8601", "browser": [{"modern_browser": "$modern_browser", '
                     '"ancient_browser": "$ancient_browser", "msie": "$msie"}], "core": [{"args": "$args", "arg": '
                     '{ "arg_example": "$arg_example"}, "body_bytes_sent": "$body_bytes_sent", "bytes_sent": '
                     '"$bytes_sent", "cookie": { "cookie_example": "$cookie_example" }, "connection": "$connection", '
                     '"connection_requests": "$connection_requests", "content_length": "$content_length", '
                     '"content_type": "$content_type", "document_root": "$document_root", "document_uri": '
                     '"$document_uri","host": "$host", "hostname": "$hostname", "http": { "http_example": '
                     '"$http_example" }, "https": "$https", "is_args": "$is_args", "limit_rate": "$limit_rate", '
                     '"msec": "$msec", "nginx_version": "$nginx_version", "pid": "$pid", "pipe": "$pipe", '
                     '"proxy_protocol_addr": "$proxy_protocol_addr", "query_string": "$query_string", "realpath_root": '
                     '"$realpath_root", "remote_addr": "$remote_addr", "remote_port": "$remote_port", "remote_user": '
                     '"$remote_user", "request": "$request", "request_body": "$request_body", "request_body_file": '
                     '"$request_body_file", "request_completion": "$request_completion", "request_filename": '
                     '"$request_filename", "request_length": "$request_length", "request_method": "$request_method", '
                     '"request_time": "$request_time", "request_uri": "$request_uri", "scheme": "$scheme", '
                     '"sent_http_": { "sent_http_example": "$sent_http_example" }, "server_addr": "$server_addr", '
                     '"server_name": "$server_name", "server_port": "$server_port", "server_protocol": '
                     '"$server_protocol", "status": "$status", "tcpinfo_rtt": "$tcpinfo_rtt", "tcpinfo_rttvar": '
                     '"$tcpinfo_rttvar", "tcpinfo_snd_cwnd": "$tcpinfo_snd_cwnd", "tcpinfo_rcv_space": '
                     '"$tcpinfo_rcv_space", "uri": "$uri" }]}')
        )

    def test_ssl(self):
        config = NginxConfig(ssl_simple_config)
        config.full_parse()
        config.run_ssl_analysis()

        ssl_certificates = config.ssl_certificates
        assert_that(ssl_certificates, has_length(1))

        # check contents
        assert_that(ssl_certificates.keys()[0], ends_with('certs.d/example.com.crt'))
        assert_that(ssl_certificates.values()[0], has_item('names'))

    def test_exclude_ssl(self):
        config = NginxConfig(ssl_simple_config)

        # also check that existing certs get cleared on subsequent parse
        config.full_parse()
        config.run_ssl_analysis()

        ssl_certificates = config.ssl_certificates
        assert_that(ssl_certificates, has_length(1))

        config.full_parse(include_ssl_certs=False)
        config.run_ssl_analysis()

        ssl_certificates = config.ssl_certificates
        assert_that(ssl_certificates, has_length(0))

    def test_regex_status_url(self):
        from re import sub as re_sub
        """
        Check that we could handle regex urls like

        location ~ /(nginx_status|status)
        location ~ ^/nginx_status$
        """
        config = NginxConfig(regex_status_config)
        config.full_parse()

        # check total amount of status urls
        assert_that(config.stub_status_urls, has_length(5))  # we have 4 valid locations in the regex_status/status.conf

        # check each location
        valid_urls_dict = {
            '1.1.1.1:80': [
                'http://1.1.1.1:80/nginx_status',
                'http://1.1.1.1:80/status',
            ],
            '1.1.1.1:81': [
                'http://1.1.1.1:81/nginx_status'
            ],
            '1.1.1.1:443': [
                'https://1.1.1.1:443/ssl_stat'
            ],
            '1.1.1.1:82': [
                'http://1.1.1.1:82/status_weird_thing',
                'http://1.1.1.1:82/nginx_status_weird_thing',
                'http://1.1.1.1:82/status_weird_some',
                'http://1.1.1.1:82/nginx_status_weird_some'
            ],
            '1.1.1.1:84': [
                'http://1.1.1.1:84/valid_location'
            ],
        }

        for url in config.stub_status_urls:
            address = re_sub('https?://', '', url)
            address = address.split('/')[0]
            valid_urls = valid_urls_dict[address]
            assert_that(valid_urls, has_item(url))

    def test_parse_wildcard_dir(self):
        """
        Tests wild card directory handling.
        """
        config = NginxConfig(wildcard_directory_config)
        config.full_parse()

        assert_that(config.directory_map, has_entries({
            '/amplify/test/fixtures/nginx/wildcard_directory/data/www/test.domain.info/config/nginx/': has_entries({
                'files': has_key(
                    '/amplify/test/fixtures/nginx/wildcard_directory/data/www/test.domain.info/config/nginx/test.conf'
                )
            }),
            '/amplify/test/fixtures/nginx/wildcard_directory/data/www/test.domain.other/config/nginx/': has_entries({
                'files': has_key(
                    '/amplify/test/fixtures/nginx/wildcard_directory/data/www/test.domain.other/config/nginx/foobar.conf'
                )
            })
        }))

    def test_logs_definitions_with_tabs(self):
        config = NginxConfig(tabs_everywhere)
        config.full_parse()

        assert_that(config.access_logs, has_key('/var/log/nginx/bbb.aaa.org.log'))

    def test_status_urls(self):
        """
        Tests that statuses are found correctly
        """
        config = NginxConfig(status_urls)
        config.full_parse()

        assert_that(config, has_property('stub_status_urls', ['http://127.0.0.1:80/', 'http://127.0.0.1:80/nginx_status']))
        assert_that(config, has_property('plus_status_external_urls', ['http://www.example.com:80/status']))
        assert_that(config, has_property('plus_status_internal_urls', ['http://127.0.0.1:80/status']))

    def test_log_format_string_concat(self):
        config = NginxConfig(log_format_string_concat)
        config.full_parse()

        expected = (
            '$remote_addr - $remote_user [$time_local] "$request" '
            '$status $body_bytes_sent "$http_referer" '
            '"$http_user_agent" "$http_x_forwarded_for" '
            '"$host" sn="$server_name" '
            'rt=$request_time '
            'ua="$upstream_addr" us="$upstream_status" '
            'ut="$upstream_response_time" ul="$upstream_response_length" '
            'cs=$upstream_cache_status'
        )

        assert_that(config.log_formats, has_length(2))
        assert_that(config.log_formats, has_entries({
            'without_newlines': expected,
            'with_newlines': expected
        }))

    def test_log_format_unicode_quote(self):
        config = NginxConfig(log_format_unicode_quote)
        config.full_parse()

        assert_that(config.log_formats, has_length(1))
        assert_that(config.log_formats, has_entries({
            'foo': 'site="$server_name" server="$host\xe2\x80\x9d uri="uri"'
        }))

    def test_log_format_with_escape_parameter(self):
        """
        Tests that the optional "escape" parameter from log_format gets ignored
        """
        config = NginxConfig(log_format_escaped_json)
        config.full_parse()
        assert_that(config.log_formats, has_length(1))
        assert_that(config.log_formats, has_key('masked'))
        assert_that(config.log_formats['masked'], not_(starts_with('escape=')))

    def test_parse_bad_access_and_error_log(self):
        """
        Test case for ignoring access_log and error_log edge cases.
        """
        config = NginxConfig(bad_log_directives_config)
        config.full_parse()

        # common structure
        assert_that(config.subtree, contains(
            has_entries({'directive': 'user'}),
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'pid'}),
            has_entries({'directive': 'events'}),
            has_entries({'directive': 'http'})
        ))

        # http
        http = config.subtree[4]['block']
        assert_that(http, has_items(
            has_entries({'directive': 'access_log', 'args': ['']}),
            has_entries({'directive': 'error_log', 'args': ['/var/log/nginx/$host-error.log']})
        ))

        assert_that(config.access_logs, empty())
        assert_that(config.error_logs, empty())


class MiscConfigTestCase(BaseTestCase):

    def test_permissions_and_mtime_affect_checksum(self):
        """
        Check that changing permissions or mtime affect checksum
        """
        config = NginxConfig(simple_config)
        config.full_parse()
        old_checksum = config.checksum()

        os.system('touch %s' % (os.getcwd() + '/test/fixtures/nginx/simple/conf.d/'))
        config.full_parse()
        new_checksum = config.checksum()
        assert_that(new_checksum, not_(equal_to(old_checksum)))


class ExcludeConfigTestCase(BaseTestCase):
    """
    Tests that .full_parse() of NginxConfig type obeys context.app_config 'exclude_logs' parameter
    """
    def test_parse_simple_exclude_dir(self):
        """Check that config.full_parse() obeys exclude_logs from app_config with directory ignore"""
        context.app_config['nginx']['exclude_logs'] = '/var/log/nginx/'

        config = NginxConfig(simple_config)
        config.full_parse()

        del context.app_config['nginx']['exclude_logs']

        assert_that(config.error_logs, empty())
        assert_that(config.access_logs, empty())

        # log formats
        assert_that(config.log_formats, has_length(1))
        assert_that(config.log_formats, has_item('super_log_format'))
        assert_that(
            config.log_formats['super_log_format'],
            equal_to(
                '$remote_addr - $remote_user [$time_local] "$request" $status ' +
                '$body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" ' +
                'rt="$request_time" ua="$upstream_addr" us="$upstream_status" ' +
                'ut="$upstream_response_time" "$gzip_ratio"'
            )
        )

        # stub status urls
        assert_that(config.stub_status_urls, has_length(2))
        assert_that(config.stub_status_urls, has_item('http://127.0.0.1:81/basic_status'))
        assert_that(config.stub_status_urls, has_item('https://127.0.0.1:443/basic_status'))

        # status urls
        assert_that(config.plus_status_external_urls, has_length(2))
        assert_that(config.plus_status_external_urls, has_item('http://127.0.0.1:81/plus_status'))
        assert_that(config.plus_status_external_urls, has_item('https://127.0.0.1:443/plus_status'))

        assert_that(config.plus_status_internal_urls, has_length(2))
        assert_that(config.plus_status_internal_urls, has_item('http://127.0.0.1:81/plus_status'))
        assert_that(config.plus_status_internal_urls, has_item('https://127.0.0.1:443/plus_status'))

    def test_parse_simple_exclude_file(self):
        """Check that config.full_parse() obeys exclude_logs from app_config with file ignore"""
        context.app_config['nginx']['exclude_logs'] = '*.log'

        config = NginxConfig(simple_config)
        config.full_parse()

        del context.app_config['nginx']['exclude_logs']

        assert_that(config.error_logs, empty())
        assert_that(config.access_logs, empty())

        # log formats
        assert_that(config.log_formats, has_length(1))
        assert_that(config.log_formats, has_item('super_log_format'))
        assert_that(
            config.log_formats['super_log_format'],
            equal_to(
                '$remote_addr - $remote_user [$time_local] "$request" $status ' +
                '$body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" ' +
                'rt="$request_time" ua="$upstream_addr" us="$upstream_status" ' +
                'ut="$upstream_response_time" "$gzip_ratio"'
            )
        )

        # stub status urls
        assert_that(config.stub_status_urls, has_length(2))
        assert_that(config.stub_status_urls, has_item('http://127.0.0.1:81/basic_status'))
        assert_that(config.stub_status_urls, has_item('https://127.0.0.1:443/basic_status'))

        # status urls
        assert_that(config.plus_status_external_urls, has_length(2))
        assert_that(config.plus_status_external_urls, has_item('http://127.0.0.1:81/plus_status'))
        assert_that(config.plus_status_external_urls, has_item('https://127.0.0.1:443/plus_status'))

        assert_that(config.plus_status_internal_urls, has_length(2))
        assert_that(config.plus_status_internal_urls, has_item('http://127.0.0.1:81/plus_status'))
        assert_that(config.plus_status_internal_urls, has_item('https://127.0.0.1:443/plus_status'))

    def test_parse_simple_exclude_combined(self):
        """Check that config.full_parse() obeys exclude_logs from app_config with combined ignore"""
        context.app_config['nginx']['exclude_logs'] = '/var/log/nginx/*.log'

        config = NginxConfig(simple_config)
        config.full_parse()

        del context.app_config['nginx']['exclude_logs']

        assert_that(config.error_logs, empty())
        assert_that(config.access_logs, empty())

        # log formats
        assert_that(config.log_formats, has_length(1))
        assert_that(config.log_formats, has_item('super_log_format'))
        assert_that(
            config.log_formats['super_log_format'],
            equal_to(
                '$remote_addr - $remote_user [$time_local] "$request" $status ' +
                '$body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" ' +
                'rt="$request_time" ua="$upstream_addr" us="$upstream_status" ' +
                'ut="$upstream_response_time" "$gzip_ratio"'
            )
        )

        # stub status urls
        assert_that(config.stub_status_urls, has_length(2))
        assert_that(config.stub_status_urls, has_item('http://127.0.0.1:81/basic_status'))
        assert_that(config.stub_status_urls, has_item('https://127.0.0.1:443/basic_status'))

        # status urls
        assert_that(config.plus_status_external_urls, has_length(2))
        assert_that(config.plus_status_external_urls, has_item('http://127.0.0.1:81/plus_status'))
        assert_that(config.plus_status_external_urls, has_item('https://127.0.0.1:443/plus_status'))

        assert_that(config.plus_status_internal_urls, has_length(2))
        assert_that(config.plus_status_internal_urls, has_item('http://127.0.0.1:81/plus_status'))
        assert_that(config.plus_status_internal_urls, has_item('https://127.0.0.1:443/plus_status'))

    def test_parse_simple_exclude_multiple(self):
        """Check that config.full_parse() obeys exclude_logs from app_config with multiple ignores"""
        context.app_config['nginx']['exclude_logs'] = '/var/log/nginx/super*.log,error*'

        config = NginxConfig(simple_config)
        config.full_parse()

        del context.app_config['nginx']['exclude_logs']

        assert_that(config.error_logs, empty())

        assert_that(config.access_logs, has_length(1))
        assert_that(config.access_logs, has_item('/var/log/nginx/access.log'))
        assert_that(config.access_logs['/var/log/nginx/access.log']['log_format'], equal_to('super_log_format'))
        assert_that(config.access_logs.values(), only_contains(
            has_entries(
                log_format=any_of(is_in(config.log_formats), none()),
                permissions=matches_regexp('[0-7]{4}'),
                readable=instance_of(bool)
            )
        ))

        # log formats
        assert_that(config.log_formats, has_length(1))
        assert_that(config.log_formats, has_item('super_log_format'))
        assert_that(
            config.log_formats['super_log_format'],
            equal_to(
                '$remote_addr - $remote_user [$time_local] "$request" $status ' +
                '$body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" ' +
                'rt="$request_time" ua="$upstream_addr" us="$upstream_status" ' +
                'ut="$upstream_response_time" "$gzip_ratio"'
            )
        )

        # stub status urls
        assert_that(config.stub_status_urls, has_length(2))
        assert_that(config.stub_status_urls, has_item('http://127.0.0.1:81/basic_status'))
        assert_that(config.stub_status_urls, has_item('https://127.0.0.1:443/basic_status'))

        # status urls
        assert_that(config.plus_status_external_urls, has_length(2))
        assert_that(config.plus_status_external_urls, has_item('http://127.0.0.1:81/plus_status'))
        assert_that(config.plus_status_external_urls, has_item('https://127.0.0.1:443/plus_status'))

        assert_that(config.plus_status_internal_urls, has_length(2))
        assert_that(config.plus_status_internal_urls, has_item('http://127.0.0.1:81/plus_status'))
        assert_that(config.plus_status_internal_urls, has_item('https://127.0.0.1:443/plus_status'))
