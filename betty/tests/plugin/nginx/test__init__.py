from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.config import Configuration, LocaleConfiguration
from betty.functools import sync
from betty.plugin.nginx import Nginx
from betty.render import render
from betty.site import Site


class NginxTest(TestCase):
    @sync
    async def test_post_render_config(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'http://example.com')
            configuration.plugins[Nginx] = {}
            async with Site(configuration) as site:
                await render(site)
            expected = '''server {
	listen 80;
	server_name example.com;
	root %s;
	add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

        set $media_type_extension html;
    index index.$media_type_extension;

        location / {
            # Handle HTTP error responses.
            error_page 401 /.error/401.$media_type_extension;
            error_page 403 /.error/403.$media_type_extension;
            error_page 404 /.error/404.$media_type_extension;
            location /.error {
                internal;
            }

            try_files $uri $uri/ =404;
        }
}''' % configuration.www_directory_path  # noqa: E101 W191
            with open(join(configuration.output_directory_path, 'nginx', 'nginx.conf')) as f:  # noqa: E101
                self.assertEquals(expected, f.read())

    @sync
    async def test_post_render_config_with_clean_urls(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'http://example.com')
            configuration.plugins[Nginx] = {}
            configuration.clean_urls = True
            async with Site(configuration) as site:
                await render(site)
            expected = '''server {
	listen 80;
	server_name example.com;
	root %s;
	add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

        set $media_type_extension html;
    index index.$media_type_extension;

        location / {
            # Handle HTTP error responses.
            error_page 401 /.error/401.$media_type_extension;
            error_page 403 /.error/403.$media_type_extension;
            error_page 404 /.error/404.$media_type_extension;
            location /.error {
                internal;
            }

            try_files $uri $uri/ =404;
        }
}''' % configuration.www_directory_path  # noqa: E101 W191
            with open(join(configuration.output_directory_path, 'nginx', 'nginx.conf')) as f:  # noqa: E101
                self.assertEquals(expected, f.read())

    @sync
    async def test_post_render_config_multilingual(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'http://example.com')
            configuration.plugins[Nginx] = {}
            configuration.locales.clear()
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            async with Site(configuration) as site:
                await render(site)
            expected = '''server {
	listen 80;
	server_name example.com;
	root %s;
	add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

        set $media_type_extension html;
    index index.$media_type_extension;

        location ~ ^/(en|nl)(/|$) {
            set $locale $1;

            add_header Content-Language "$locale" always;

            # Handle HTTP error responses.
            error_page 401 /$locale/.error/401.$media_type_extension;
            error_page 403 /$locale/.error/403.$media_type_extension;
            error_page 404 /$locale/.error/404.$media_type_extension;
            location ~ ^/$locale/\.error {
                internal;
            }

            try_files $uri $uri/ =404;
        }
        location @localized_redirect {
                set $locale_alias en;
            return 301 /$locale_alias$uri;
        }
        location / {
            try_files $uri @localized_redirect;
        }
}''' % configuration.www_directory_path  # noqa: E101 W191
            with open(join(configuration.output_directory_path, 'nginx', 'nginx.conf')) as f:  # noqa: E101
                self.assertEquals(expected, f.read())

    @sync
    async def test_post_render_config_multilingual_with_content_negotiation(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'http://example.com')
            configuration.content_negotiation = True
            configuration.plugins[Nginx] = {}
            configuration.locales.clear()
            configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
            configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
            async with Site(configuration) as site:
                await render(site)
            expected = '''server {
	listen 80;
	server_name example.com;
	root %s;
	add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

        set_by_lua_block $media_type_extension {
            local available_media_types = {'text/html', 'application/json'}
            local media_type_extensions = {}
            media_type_extensions['text/html'] = 'html'
            media_type_extensions['application/json'] = 'json'
            local media_type = require('cone').negotiate(ngx.req.get_headers()['Accept'], available_media_types)
            return media_type_extensions[media_type]
        }
    index index.$media_type_extension;

        location ~ ^/(en|nl)(/|$) {
            set $locale $1;

            add_header Content-Language "$locale" always;

            # Handle HTTP error responses.
            error_page 401 /$locale/.error/401.$media_type_extension;
            error_page 403 /$locale/.error/403.$media_type_extension;
            error_page 404 /$locale/.error/404.$media_type_extension;
            location ~ ^/$locale/\.error {
                internal;
            }

            try_files $uri $uri/ =404;
        }
        location @localized_redirect {
                set_by_lua_block $locale_alias {
                    local available_locales = {'en-US', 'nl-NL'}
                    local locale_aliases = {}
                        locale_aliases['en-US'] = 'en'
                        locale_aliases['nl-NL'] = 'nl'
                    local locale = require('cone').negotiate(ngx.req.get_headers()['Accept-Language'], available_locales)
                    return locale_aliases[locale]
                }
            return 301 /$locale_alias$uri;
        }
        location / {
            try_files $uri @localized_redirect;
        }
}''' % configuration.www_directory_path  # noqa: E101 W191
            with open(join(configuration.output_directory_path, 'nginx', 'nginx.conf')) as f:  # noqa: E101
                self.assertEquals(expected, f.read())

    @sync
    async def test_post_render_config_with_content_negotiation(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'http://example.com')
            configuration.content_negotiation = True
            configuration.plugins[Nginx] = {}
            async with Site(configuration) as site:
                await render(site)
            expected = '''server {
	listen 80;
	server_name example.com;
	root %s;
	add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

        set_by_lua_block $media_type_extension {
            local available_media_types = {'text/html', 'application/json'}
            local media_type_extensions = {}
            media_type_extensions['text/html'] = 'html'
            media_type_extensions['application/json'] = 'json'
            local media_type = require('cone').negotiate(ngx.req.get_headers()['Accept'], available_media_types)
            return media_type_extensions[media_type]
        }
    index index.$media_type_extension;

        location / {
            # Handle HTTP error responses.
            error_page 401 /.error/401.$media_type_extension;
            error_page 403 /.error/403.$media_type_extension;
            error_page 404 /.error/404.$media_type_extension;
            location /.error {
                internal;
            }

            try_files $uri $uri/ =404;
        }
}''' % configuration.www_directory_path  # noqa: E101 W191
            with open(join(configuration.output_directory_path, 'nginx', 'nginx.conf')) as f:  # noqa: E101
                self.assertEquals(expected, f.read())

    @sync
    async def test_post_render_config_with_https(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Nginx] = {}
            async with Site(configuration) as site:
                await render(site)
            expected = '''    server {
        listen 80;
        server_name example.com;
        return 301 https://$host$request_uri;
    }
server {
	listen 443 ssl http2;
	server_name example.com;
	root %s;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
	add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

        set $media_type_extension html;
    index index.$media_type_extension;

        location / {
            # Handle HTTP error responses.
            error_page 401 /.error/401.$media_type_extension;
            error_page 403 /.error/403.$media_type_extension;
            error_page 404 /.error/404.$media_type_extension;
            location /.error {
                internal;
            }

            try_files $uri $uri/ =404;
        }
}''' % configuration.www_directory_path  # noqa: E101 W191
            with open(join(configuration.output_directory_path, 'nginx', 'nginx.conf')) as f:  # noqa: E101
                self.assertEquals(expected, f.read())
