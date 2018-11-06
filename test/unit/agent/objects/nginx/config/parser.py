# -*- coding: utf-8 -*-
import os

from hamcrest import *

from amplify.agent.objects.nginx.config.parser import NginxConfigParser, IGNORED_DIRECTIVES
from test.base import BaseTestCase, BaseControllerTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"

simple_config = os.getcwd() + '/test/fixtures/nginx/simple/nginx.conf'
complex_config = os.getcwd() + '/test/fixtures/nginx/complex/nginx.conf'
huge_config = os.getcwd() + '/test/fixtures/nginx/huge/nginx.conf'
rewrites_config = os.getcwd() + '/test/fixtures/nginx/rewrites/nginx.conf'
map_lua_perl = os.getcwd() + '/test/fixtures/nginx/map_lua_perl/nginx.conf'
ssl_broken_config = os.getcwd() + '/test/fixtures/nginx/ssl/broken/nginx.conf'
includes_config = os.getcwd() + '/test/fixtures/nginx/includes/nginx.conf'
windows_config = os.getcwd() + '/test/fixtures/nginx/windows/nginx.conf'
json_config = os.getcwd() + '/test/fixtures/nginx/custom/json.conf'
ssl_simple_config = os.getcwd() + '/test/fixtures/nginx/ssl/simple/nginx.conf'
sub_filter_config = os.getcwd() + '/test/fixtures/nginx/custom/sub_filter.conf'
proxy_pass_config = os.getcwd() + '/test/fixtures/nginx/custom/proxy_pass.conf'
quoted_location_with_semicolon = os.getcwd() + '/test/fixtures/nginx/quoted_location_with_semicolon/nginx.conf'
complex_add_header = os.getcwd() + '/test/fixtures/nginx/complex_add_header/nginx.conf'
escaped_string_config = os.getcwd() + '/test/fixtures/nginx/custom/escaped_string.conf'
tabs_everywhere = os.getcwd() + '/test/fixtures/nginx/tabs/nginx.conf'
more_clean_headers = os.getcwd() + '/test/fixtures/nginx/more_clean_headers/nginx.conf'
location_with_semicolon_equal = os.getcwd() + '/test/fixtures/nginx/location_with_semicolon_equal/nginx.conf'


class ParserTestCase(BaseTestCase):

    # line number for stub status may be off?  69 not 68...
    def test_parse_simple(self):
        cfg = NginxConfigParser(simple_config)

        cfg.parse()
        subtree = cfg.simplify()

        # main context
        assert_that(subtree, contains(
            has_entries({'directive': 'user'}),
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'pid'}),
            has_entries({
                'directive': 'events',
                'block': contains(
                    has_entries({'directive': 'worker_connections'})
                )
            }),
            has_entries({
                'directive': 'http',
                'block': contains(
                    # from nginx.conf
                    has_entries({'directive': 'sendfile'}),
                    has_entries({'directive': 'tcp_nopush'}),
                    has_entries({'directive': 'tcp_nodelay'}),
                    has_entries({'directive': 'keepalive_timeout'}),
                    has_entries({'directive': 'types_hash_max_size'}),
                    has_entries({'directive': 'include', 'args': ['mime.types']}),

                    # from mime.types
                    has_entries({
                        'directive': 'types',
                        'block': has_item(
                            has_entries({'directive': 'application/java-archive'})
                        )
                    }),

                    # back to nginx.conf
                    has_entries({'directive': 'default_type'}),
                    has_entries({'directive': 'proxy_buffering'}),
                    has_entries({'directive': 'log_format'}),
                    has_entries({'directive': 'access_log'}),
                    has_entries({'directive': 'error_log'}),
                    has_entries({'directive': 'gzip'}),
                    has_entries({'directive': 'gzip_disable'}),
                    has_entries({'directive': 'include', 'args': ['conf.d/*.conf']}),

                    # from conf.d/something.conf
                    has_entries({'directive': 'upstream'}),
                    has_entries({
                        'directive': 'server',
                        'block': contains(
                            has_entries({'directive': 'listen'}),
                            has_entries({'directive': 'index'}),
                            has_entries({'directive': 'access_log'}),
                            has_entries({
                                'directive': 'location',
                                'args': ['/'],
                                'block': contains(
                                    has_entries({'directive': 'proxy_pass'}),
                                    has_entries({
                                        'directive': 'location',
                                        'args': ['/foo'],
                                        'block': []
                                    })
                                )
                            })
                        )
                    }),
                    has_entries({
                        'directive': 'add_header',
                        'args': ['Strict-Transport-Security', 'max-age=31536000; includeSubdomains; ;preload']
                    }),

                    # back to nginx.conf
                    has_entries({
                        'directive': 'server',
                        'block': contains(
                            has_entries({'directive': 'server_name'}),
                            has_entries({'directive': 'listen', 'args': ['81', 'default_server']}),
                            has_entries({
                                'directive': 'location',
                                'args': ['/basic_status'],
                                'block': contains(
                                    has_entries({'directive': 'proxy_request_buffering'}),
                                    has_entries({'directive': 'stub_status'})
                                )
                            }),
                            has_entries({
                                'directive': 'location',
                                'args': ['/plus_status'],
                                'block': contains(
                                    has_entries({'directive': 'status'})
                                )
                            }),
                            has_entries({
                                'directive': 'location',
                                'args': ['/api'],
                                'block': contains(
                                    has_entries({'directive': 'api', 'args': ['write=on']})
                                )
                            }),
                            has_entries({'directive': 'rewrite', 'args': ['^', 'http://www.domain.com']})
                        )
                    }),

                    has_entries({
                        'directive': 'server',
                        'block': contains(
                            has_entries({'directive': 'server_name'}),
                            has_entries({'directive': 'listen', 'args': ['443', 'ssl']}),
                            has_entries({
                                'directive': 'location',
                                'args': ['/basic_status'],
                                'block': contains(
                                    has_entries({'directive': 'proxy_request_buffering'}),
                                    has_entries({'directive': 'stub_status'})
                                )
                            }),
                            has_entries({
                                'directive': 'location',
                                'args': ['/plus_status'],
                                'block': contains(
                                    has_entries({'directive': 'status'})
                                )
                            }),
                            has_entries({
                                'directive': 'location',
                                'args': ['/api'],
                                'block': contains(
                                    has_entries({'directive': 'api'})
                                )
                            }),
                            has_entries({'directive': 'rewrite', 'args': ['^', 'http://www.domain.com']})
                        )
                    })
                )
            })
        ))

    def test_parse_huge(self):
        cfg = NginxConfigParser(huge_config)

        cfg.parse()
        subtree = cfg.simplify()

        # common structure
        assert_that(subtree, contains(
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'error_log'}),
            has_entries({'directive': 'events'}),
            has_entries({'directive': 'http'})
        ))

        # http
        http = subtree[3]['block']
        assert_that(http, contains(
            has_entries({'directive': 'include', 'args': ['mime.types']}),
            has_entries({'directive': 'types', 'block': has_length(70)}),
            has_entries({'directive': 'include', 'args': ['mime.types2']}),
            has_entries({'directive': 'default_type'}),
            has_entries({'directive': 'log_format'}),
            has_entries({'directive': 'access_log'}),
            has_entries({'directive': 'sendfile'}),
            has_entries({'directive': 'keepalive_timeout'}),
            has_entries({'directive': 'reset_timedout_connection'}),
            has_entries({'directive': 'map_hash_max_size'}),
            has_entries({'directive': 'map', 'args': ['$dirname', '$diruri']}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'server_name', 'args': ['_']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'server_name', 'args': ['pp.nginx.com']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'server_name', 'args': ['nginx.org']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'server_name', 'args': ['nginx.net', 'www.nginx.net']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'server_name', 'args': ['www.nginx.org']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'server_name', 'args': ['www.nginx.com']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'server_name', 'args': ['nginx.com']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'server_name', 'args': ['nginx.ru', 'www.nginx.ru']}))}),

        ))

        # map
        http_map = http[10]['block']
        assert_that(http_map, contains(
            has_entries({'directive': 'default', 'args': ['dirindex.html']}),
            has_entries({'directive': 'include', 'args': ['dir.map'], 'includes': []})
        ))

        # nginx.org server
        nginx_org_server = http[13]['block']
        assert_that(nginx_org_server, contains(
            has_entries({'directive': 'listen'}),
            has_entries({'directive': 'listen'}),
            has_entries({'directive': 'server_name'}),
            has_entries({'directive': 'charset'}),
            has_entries({'directive': 'gzip_static'}),
            has_entries({'directive': 'access_log'}),
            has_entries({'directive': 'root'}),
            has_entries({'directive': 'location', 'args': ['~', '/\.svn']}),
            has_entries({'directive': 'location', 'args': ['~', '/\.hg']}),
            has_entries({'directive': 'location', 'args': ['/']}),
            has_entries({'directive': 'location', 'args': ['/download/']}),
            has_entries({'directive': 'location', 'args': ['/patches/']}),
            has_entries({'directive': 'location', 'args': ['/packages/']}),
            has_entries({'directive': 'location', 'args': ['/sshkeys/']}),
            has_entries({'directive': 'location', 'args': ['/packages/aws/']}),
            has_entries({'directive': 'location', 'args': ['/packages/aws.amazon-linux/']}),
            has_entries({'directive': 'location', 'args': ['/packages/aws.amazon-linux.sms/']}),
            has_entries({'directive': 'location', 'args': ['/packages/aws.ubuntu/']}),
            has_entries({'directive': 'location', 'args': ['/packages/aws.ubuntu.sms/']}),
            has_entries({'directive': 'location', 'args': ['/packages/azure.ubuntu/']}),
            has_entries({'directive': 'location', 'args': ['/packages/gce.ubuntu/']}),
            has_entries({'directive': 'location', 'args': ['/books/'], 'line': 135}),
            has_entries({'directive': 'location', 'args': ['/r/']}),
            has_entries({'directive': 'location', 'args': ['/en/CHANGES']}),
            has_entries({'directive': 'location', 'args': ['/ru/CHANGES.ru']}),
            has_entries({'directive': 'location', 'args': ['=', '/LICENSE']}),
            has_entries({'directive': 'location', 'args': ['=', '/LICENSE.ru']}),
            has_entries({'directive': 'location', 'args': ['/docs/']}),
            has_entries({'directive': 'location', 'args': ['~', '^/(en|ru|tr|cn|he|ja)/docs/introduction.html$']}),
            has_entries({'directive': 'location', 'args': ['~', '^/(ru|tr)/docs/howto.html$']}),
            has_entries({'directive': 'location', 'args': ['~', '^/(en|cn|he|ja)/docs/howto.html$']}),
            has_entries({'directive': 'location', 'args': ['~', '^/([a-z][a-z])/docs/.*/$']}),
            has_entries({'directive': 'location', 'args': ['=', '/mailman']}),
            has_entries({'directive': 'location', 'args': ['=', '/mailman/']}),
            has_entries({'directive': 'location', 'args': ['/mailman/']}),
            has_entries({'directive': 'location', 'args': ['=', '/pipermail']}),
            has_entries({'directive': 'location', 'args': ['=', '/pipermail/']}),
            has_entries({'directive': 'location', 'args': ['/pipermail/']}),
            has_entries({'directive': 'location', 'args': ['=', '/en/docs/stream/ngx_stream_module.html']}),
            has_entries({'directive': 'location', 'args': ['=', '/en/docs/howto_setup_development_environment_on_ec2.html']}),
            has_entries({'directive': 'location', 'args': ['=', '/404.html']}),
            has_entries({'directive': 'location', 'args': ['=', '/50x.html']}),
            has_entries({'directive': 'location', 'args': ['/ru/']}),
            has_entries({'directive': 'location', 'args': ['/cn/']}),
            has_entries({'directive': 'location', 'args': ['/he/']}),
            has_entries({'directive': 'location', 'args': ['/it/']}),
            has_entries({'directive': 'location', 'args': ['/ja/']}),
            has_entries({'directive': 'location', 'args': ['/tr/']}),
            has_entries({'directive': 'location', 'args': ['@en_redirect']}),
            has_entries({'directive': 'error_page', 'args': ['403', '404', '/404.html']}),
            has_entries({'directive': 'error_page', 'args': ['502', '504', '/50x.html']}),
            has_entries({'directive': 'location', 'args': ['/libxslt/']}),
            has_entries({'directive': 'location', 'args': ['/tmp/']}),
        ))

        # check directory map
        assert_that(cfg.directory_map, has_key('/amplify/test/fixtures/nginx/huge/'))
        for key in ('info', 'files'):
            assert_that(cfg.directory_map['/amplify/test/fixtures/nginx/huge/'], has_key(key))

        files = cfg.directory_map['/amplify/test/fixtures/nginx/huge/']['files']
        assert_that(files, has_length(7))

    def test_parse_complex(self):
        cfg = NginxConfigParser(complex_config)

        cfg.parse()
        tree = cfg.simplify()

        # common structure
        assert_that(tree, contains(
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'daemon'}),
            has_entries({'directive': 'events'}),
            has_entries({'directive': 'http'}),
        ))

        # http
        http = tree[3]['block']
        assert_that(http, contains(
            # main config file
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.1.0.1']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.2.0.1:10122']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.3.0.1:10122']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.4.0.1:10122']}))}),
            has_entries({'directive': 'upstream'}),
            has_entries({'directive': 'resolver'}),

            # part.conf
            has_entries({'directive': 'include', 'args': ['part.conf']}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.0.0.1:1234']}))}),

            # part2.conf
            has_entries({'directive': 'include', 'args': ['part2.conf']}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.6.1.1:10122']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.7.2.1:10122']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.8.3.1:10122']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.9.4.1:10122']}))}),

            # back to the main config
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.0.0.1:10122']}))}),
            has_entries({'directive': 'types'}),
            has_entries({'directive': 'upstream'}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['127.0.0.3:10122']}))}),
            has_entries({'directive': 'map'}),
            has_entries({'directive': 'upstream'}),
        ))

    def test_parse_rewrites(self):
        cfg = NginxConfigParser(rewrites_config)

        cfg.parse()
        subtree = cfg.simplify()

        # common structure
        assert_that(subtree, contains(
            has_entries({'directive': 'user'}),
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'worker_rlimit_nofile'}),
            has_entries({'directive': 'error_log'}),
            has_entries({'directive': 'pid'}),
            has_entries({'directive': 'events'}),
            has_entries({'directive': 'http'})
        ))

        # http
        http = subtree[6]['block']
        assert_that(http, contains(
            has_entries({'directive': 'include', 'args': ['mime.types']}),
            has_entries({'directive': 'default_type'}),
            has_entries({'directive': 'access_log'}),
            has_entries({'directive': 'proxy_cache_path'}),
            has_entries({'directive': 'fastcgi_cache_path'}),
            has_entries({'directive': 'sendfile'}),
            has_entries({'directive': 'keepalive_timeout'}),
            has_entries({'directive': 'tcp_nodelay'}),
            has_entries({'directive': 'fastcgi_buffers'}),
            has_entries({'directive': 'fastcgi_buffering'}),
            has_entries({'directive': 'fastcgi_buffer_size'}),
            has_entries({'directive': 'proxy_buffers'}),
            has_entries({'directive': 'proxy_buffer_size'}),
            has_entries({'directive': 'upstream'}),
            has_entries({'directive': 'gzip'}),
            has_entries({'directive': 'log_format'}),
            has_entries({'directive': 'include', 'args': ['sites-enabled/*.conf']}),
            has_entries({
                'directive': 'server',
                'block': has_items(
                    has_entries({'directive': 'server_name', 'args': ['mb.some.org', 'localhost', 'melchior', 'melchior.some.org']}),
                    has_entries({'directive': 'include', 'args': ['sites-enabled/rewrites']}),
                    has_entries({'directive': 'rewrite'})
                )
            })
        ))

    def test_parse_map_lua_perl(self):
        cfg = NginxConfigParser(map_lua_perl)

        cfg.parse()
        subtree = cfg.simplify()

        # common structure
        assert_that(subtree, contains(
            has_entries({'directive': 'user'}),
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'pid'}),
            has_entries({'directive': 'events'}),
            has_entries({'directive': 'http'})
        ))

        # http
        http = subtree[4]['block']
        assert_that(http, contains(
            has_entries({'directive': 'sendfile'}),
            has_entries({'directive': 'tcp_nopush'}),
            has_entries({'directive': 'tcp_nodelay'}),
            has_entries({'directive': 'keepalive_timeout'}),
            has_entries({'directive': 'types_hash_max_size'}),
            has_entries({'directive': 'default_type'}),
            has_entries({'directive': 'proxy_buffering'}),
            has_entries({'directive': 'log_format'}),
            has_entries({'directive': 'access_log'}),
            has_entries({'directive': 'error_log'}),
            has_entries({'directive': 'include', 'args': ['map.conf']}),
            has_entries({'directive': 'map', 'args': ['$http_x_forwarded_proto', '$enr_scheme']}),
            has_entries({'directive': 'map', 'args': ['$http_user_agent', '$enr_browser']}),
            has_entries({'directive': 'map', 'args': ['$http_user_agent', '$enr_device']}),
            has_entries({'directive': 'map', 'args': ['$http_user_agent', '$enr_os']}),
            has_entries({'directive': 'map', 'args': ['$http_referer', '$bad_referer']}),
            has_entries({'directive': 'include', 'args': ['perl.conf']}),
            has_entries({'directive': 'perl_set'}),
            has_entries({'directive': 'perl_set'}),
            has_entries({'directive': 'perl_set'}),
            has_entries({'directive': 'perl_set'}),
            has_entries({'directive': 'perl_set'}),
            has_entries({'directive': 'perl_set'}),
            has_entries({'directive': 'perl_set'}),
            has_entries({'directive': 'perl_set'}),
            has_entries({'directive': 'perl_set'}),
            has_entries({'directive': 'include', 'args': ['supermap.conf']}),
            has_entries({'directive': 'map', 'args': ['$http_user_agent', '$device']}),
            has_entries({'directive': 'server'})
        ))

        # check some maps
        referer_map = http[15]['block']
        assert_that(referer_map, has_item(
            has_entries({'directive': '~* move-', 'args': ['$validate_referer']})
        ))

        supermap_map = http[27]['block']
        assert_that(supermap_map, has_item(
            has_entries({'directive': '~*Nexus\\ One|Nexus\\ S', 'args': ['m']})
        ))

        # local server
        server = http[28]['block']
        assert_that(server, contains(
            has_entries({'directive': 'server_name', 'args': ['127.0.0.1']}),
            has_entries({'directive': 'listen'}),
            has_entries({'directive': 'location', 'args': ['/basic_status']}),
            has_entries({'directive': 'location', 'args': ['/plus_status']}),
            has_entries({'directive': 'include', 'args': ['lua.conf']}),
            has_entries({'directive': 'lua_package_path'}),
            has_entries({'directive': 'lua_shared_dict'}),
            has_entries({'directive': 'location', 'args': ['=', '/some/']}),
            has_entries({'directive': 'rewrite'})
        ))

        # /some/ location
        location = server[7]['block']
        assert_that(location, contains(
            has_entries({'directive': 'log_not_found'}),
            has_entries({'directive': 'expires'}),
            has_entries({'directive': 'root'}),
            has_entries({'directive': 'set'}),
            has_entries({'directive': 'set'}),
            has_entries({'directive': 'rewrite_by_lua'})
        ))

    def test_parse_ssl(self):
        """
        This test case specifically checks to see that none of the excluded directives (SSL focused) are parsed.
        """
        cfg = NginxConfigParser(ssl_broken_config)

        cfg.parse()
        subtree = cfg.simplify()

        # common structure
        assert_that(subtree, contains(
            has_entries({'directive': 'http'})
        ))

        # http
        http = subtree[0]['block']
        assert_that(http, contains(
            has_entries({'directive': 'server'}),
            has_entries({'directive': 'server'})
        ))

        # ssl server
        ssl_server = http[1]['block']

        # check that ignored directives were actually ignored
        for directive in IGNORED_DIRECTIVES:
            assert_that(ssl_server, not_(has_item(has_entries({'directive': directive}))))

        assert_that(ssl_server, has_item(
            has_entries({'directive': 'ssl_certificate', 'args': ['certs.d/example.cert']})
        ))

    def test_lightweight_parse_includes(self):
        # simple
        cfg = NginxConfigParser(simple_config)
        files, directories = cfg.get_structure()
        assert_that(files.keys(), contains_inanyorder(
            '/amplify/test/fixtures/nginx/simple/conf.d/something.conf',
            '/amplify/test/fixtures/nginx/simple/mime.types',
            '/amplify/test/fixtures/nginx/simple/nginx.conf'
        ))
        assert_that(directories.keys(), contains_inanyorder(
            '/amplify/test/fixtures/nginx/simple/',
            '/amplify/test/fixtures/nginx/simple/conf.d/'
        ))

        # includes
        cfg = NginxConfigParser(includes_config)
        files, directories = cfg.get_structure()
        assert_that(files.keys(), contains_inanyorder(
            '/amplify/test/fixtures/nginx/includes/conf.d/something.conf',
            '/amplify/test/fixtures/nginx/includes/mime.types',
            '/amplify/test/fixtures/nginx/includes/conf.d/additional.conf',
            '/amplify/test/fixtures/nginx/includes/conf.d/include.conf',
            '/amplify/test/fixtures/nginx/includes/nginx.conf'
        ))
        assert_that(directories.keys(), contains_inanyorder(
            '/amplify/test/fixtures/nginx/includes/',
            '/amplify/test/fixtures/nginx/includes/conf.d/'
        ))

    def test_parse_windows(self):
        """
        Test that windows style line endings are replaces with Unix style ones for parser.
        """
        cfg = NginxConfigParser(windows_config)

        cfg.parse()
        subtree = cfg.simplify()

        # common structure
        assert_that(subtree, contains(
            has_entries({'directive': 'user'}),
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'worker_rlimit_nofile'}),
            has_entries({'directive': 'events'}),
            has_entries({'directive': 'error_log'}),
            has_entries({'directive': 'pid'}),
            has_entries({'directive': 'http'})
        ))

        http = subtree[6]['block']
        assert_that(http, contains(
            has_entries({'directive': 'server_tokens'}),
            has_entries({'directive': 'include', 'args': ['mime.types']}),
            has_entries({'directive': 'default_type'}),
            has_entries({'directive': 'charset_types'}),
            has_entries({'directive': 'log_format'}),
            has_entries({'directive': 'access_log'}),
            has_entries({'directive': 'keepalive_timeout'}),
            has_entries({'directive': 'sendfile'}),
            has_entries({'directive': 'tcp_nopush'}),
            has_entries({'directive': 'gzip'}),
            has_entries({'directive': 'gzip_comp_level'}),
            has_entries({'directive': 'gzip_min_length'}),
            has_entries({'directive': 'gzip_proxied'}),
            has_entries({'directive': 'gzip_vary'}),
            has_entries({
                'directive': 'gzip_types',
                'args': contains(
                    'application/atom+xml', 'application/javascript', 'application/json', 'application/ld+json',
                    'application/manifest+json', 'application/rss+xml', 'application/vnd.geo+json',
                    'application/vnd.ms-fontobject', 'application/x-font-ttf', 'application/x-web-app-manifest+json',
                    'application/xhtml+xml', 'application/xml', 'font/opentype', 'image/bmp',
                    'image/svg+xml', 'image/x-icon', 'text/cache-manifest', 'text/css', 'text/plain',
                    'text/vcard', 'text/vnd.rim.location.xloc', 'text/vtt', 'text/x-component',
                    'text/x-cross-domain-policy'
                )
            }),
            has_entries({'directive': 'include', 'args': ['sites-enabled/*']}),
        ))

    def test_parse_json(self):
        """
        Test json config format.  This is the first test investigating Parser auto-escape problems.
        """
        cfg = NginxConfigParser(json_config)

        cfg.parse()
        subtree = cfg.simplify()

        # common structure
        assert_that(subtree, contains(
            has_entries({'directive': 'user'}),
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'error_log'}),
            has_entries({'directive': 'pid'}),
            has_entries({'directive': 'events'}),
            has_entries({'directive': 'http'})
        ))

        http = subtree[5]['block']
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
        assert_that(log_format_args[0], equal_to('json'))
        assert_that(log_format_args[1].find('\\'), equal_to(-1))

    def test_parse_ssl_simple_config(self):
        cfg = NginxConfigParser(ssl_simple_config)

        cfg.parse()
        subtree = cfg.simplify()

        # common structure
        assert_that(subtree, contains(
            has_entries({'directive': 'user'}),
            has_entries({'directive': 'worker_processes'}),
            has_entries({'directive': 'pid'}),
            has_entries({'directive': 'events'}),
            has_entries({'directive': 'http'})
        ))

        http = subtree[4]['block']
        assert_that(http, contains(
            has_entries({'directive': 'sendfile'}),
            has_entries({'directive': 'tcp_nopush'}),
            has_entries({'directive': 'tcp_nodelay'}),
            has_entries({'directive': 'keepalive_timeout'}),
            has_entries({'directive': 'types_hash_max_size'}),
            has_entries({'directive': 'include', 'args': ['mime.types']}),
            has_entries({'directive': 'types', 'block': has_length(70)}),
            has_entries({'directive': 'default_type'}),
            has_entries({'directive': 'proxy_buffering'}),
            has_entries({'directive': 'log_format'}),
            has_entries({'directive': 'access_log'}),
            has_entries({'directive': 'error_log'}),
            has_entries({'directive': 'gzip'}),
            has_entries({'directive': 'gzip_disable'}),
            has_entries({'directive': 'include', 'args': ['conf.d/*.conf']}),
            # from conf.d/something.conf
            has_entries({'directive': 'upstream'}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['4000']}))}),
            # from conf.d/ssl.conf
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['80']}))}),
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['443', 'ssl']}))}),
            # back in nginx.conf
            has_entries({'directive': 'server', 'block': has_item(has_entries({'directive': 'listen', 'args': ['81', 'default_server']}))}),
        ))

        # check that ignored directives were actually ignored in all servers
        for server_directive in http[16:20]:
            server = server_directive['block']
            for directive in IGNORED_DIRECTIVES:
                assert_that(server, not_(has_item(has_entries({'directive': directive}))))

        # check ssl settings for specifically the ssl server block
        ssl_server = http[18]['block']
        assert_that(ssl_server, has_items(
            has_entries({'directive': 'server_name', 'args': ['example.com']}),
            has_entries({'directive': 'ssl_certificate', 'args': ['certs.d/example.com.crt']})
        ))

        assert_that(cfg.ssl_certificates, has_length(1))

    def test_lightweight_parse_includes_permissions(self):
        """
        Checks that we get file permissions during lightweight parsing
        """
        cfg = NginxConfigParser(simple_config)
        files, directories = cfg.get_structure()

        test_file = '/amplify/test/fixtures/nginx/simple/conf.d/something.conf'
        size = os.path.getsize(test_file)
        mtime = int(os.path.getmtime(test_file))
        permissions = oct(os.stat(test_file).st_mode & 0777)

        assert_that(
            files[test_file],
            equal_to({'size': size, 'mtime': mtime, 'permissions': permissions})
        )

        test_directory = '/amplify/test/fixtures/nginx/simple/conf.d/'
        size = os.path.getsize(test_directory)
        mtime = int(os.path.getmtime(test_directory))
        permissions = oct(os.stat(test_directory).st_mode & 0777)

        assert_that(
            directories[test_directory],
            equal_to({'size': size, 'mtime': mtime, 'permissions': permissions})
        )

    def test_sub_filter(self):
        cfg = NginxConfigParser(sub_filter_config)

        cfg.parse()
        subtree = cfg.simplify()

        # common structure
        assert_that(subtree, contains(
            has_entries({'directive': 'http'})
        ))

        http = subtree[0]['block']
        assert_that(http, contains(
            has_entries({'directive': 'gzip'}),
            has_entries({'directive': 'gzip_disable'}),
            has_entries({'directive': 'sub_filter', 'args': ['foo', 'bar']}),
            has_entries({'directive': 'sub_filter', 'args': ['https://foo.example.com/1', 'https://bar.example.com/1']}),
            has_entries({'directive': 'sub_filter', 'args': ['https://foo.example.com/2', 'https://bar.example.com/2']}),
            has_entries({'directive': 'sub_filter', 'args': ['https://foo.example.com/3', 'https://bar.example.com/3']}),
            has_entries({
                'directive': 'sub_filter',
                'args': [
                    '</body>',
                    '<p style="position: fixed;top:\n            60px;width:100%;;background-color: #f00;background-color:\n            rgba(255,0,0,0.5);color: #000;text-align: center;font-weight:\n            bold;padding: 0.5em;z-index: 1;">Test</p></body>'
                ]
            })
        ))

    def test_proxy_pass(self):
        cfg = NginxConfigParser(proxy_pass_config)

        cfg.parse()
        subtree = cfg.simplify()

        # common structure
        assert_that(subtree, contains(
            has_entries({'directive': 'http'})
        ))

        http = subtree[0]['block']
        assert_that(http, contains(
            has_entries({'directive': 'gzip'}),
            has_entries({'directive': 'gzip_disable'}),
            has_entries({'directive': 'server'})
        ))

        server = http[2]['block']
        assert_that(server, contains(
            has_entries({'directive': 'location', 'args': ['/']})
        ))

        location = server[0]['block']
        assert_that(location, contains(
            has_entries({'directive': 'proxy_pass', 'args': ['$scheme://${scheme}site.com_backend']})
        ))

    def test_quoted_location_with_semicolon(self):
        cfg = NginxConfigParser(quoted_location_with_semicolon)
        assert_that(calling(cfg.parse), not_(raises(TypeError)))

    def test_complex_add_header(self):
        """Test complex definitions for add_header are parsed correctly"""
        cfg = NginxConfigParser(complex_add_header)
        cfg.parse()

        assert_that(cfg.errors, has_length(0))

    def test_escaped_string(self):
        cfg = NginxConfigParser(escaped_string_config)
        cfg.parse()

        assert_that(cfg.errors, empty())

        subtree = cfg.simplify()
        assert_that(subtree, contains(
            has_entries({
                'directive': 'http',
                'block': contains(
                    has_entries({
                        'directive': 'server',
                        'block': contains(
                            has_entries({
                                'directive': 'add_header',
                                'args': ['LinkOne', '<https://$http_host$request_uri>; rel="foo"'],
                            }),
                            has_entries({
                                'directive': 'add_header',
                                'args': ['LinkTwo', "<https://$http_host$request_uri>; rel='bar'"],
                            })
                        )
                    })
                )
            })
        ))

    def test_tabs_everywhere(self):
        cfg = NginxConfigParser(tabs_everywhere)
        cfg.parse()
        assert_that(cfg.errors, has_length(0))

    def test_more_clean_headers(self):
        cfg = NginxConfigParser(more_clean_headers)
        cfg.parse()
        assert_that(cfg.errors, has_length(0))

    def test_location_with_semicolon_equal(self):
        cfg = NginxConfigParser(location_with_semicolon_equal)
        assert_that(calling(cfg.parse), not_(raises(TypeError)))
        assert_that(cfg.errors, has_length(0))


class ControllerParserTestCase(BaseControllerTestCase):
    def test_parse_ssl_not_ignored(self):
        """
        This test case specifically checks to see that excluded directives (SSL focused) are parsed
        for controller agent
        """
        cfg = NginxConfigParser(ssl_broken_config)

        cfg.parse()
        subtree = cfg.simplify()

        http = subtree[0]['block']
        ssl_server = http[1]['block']
        # check that ignored directives were not ignored
        # ssl_certificate_key is one of the IGNORED_DIRECTIVE
        assert_that(ssl_server, has_item(
            has_entries({'directive': 'ssl_certificate_key'}),
        ))

    def test_parse_ssl_simple_config_not_ignored(self):
        cfg = NginxConfigParser(ssl_simple_config)

        cfg.parse()
        subtree = cfg.simplify()

        http = subtree[4]['block']

        # check that ignored directives were not ignored
        # ssl_certificate_key, ssl_trusted_certificate are some of the the IGNORED_DIRECTIVE
        # check ssl settings for specifically the ssl server block
        ssl_server = http[18]['block']
        assert_that(ssl_server, has_items(
            has_entries({'directive': 'ssl_certificate_key'}),
            has_entries({'directive': 'ssl_trusted_certificate'})
        ))

        assert_that(cfg.ssl_certificates, has_length(1))
