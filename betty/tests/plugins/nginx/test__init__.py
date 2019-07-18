from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.config import Configuration
from betty.plugins.nginx import Nginx
from betty.render import render
from betty.site import Site


class NginxTest(TestCase):
    def test_post_render_config_without_clean_urls(self):
        self.maxDiff = None

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Nginx] = {}
            site = Site(configuration)
            render(site)
            expected = '''server {
	# The port to listen to.
	listen 80;
	# The publicly visible hostname.
	server_name example.com;
	# The path to the local web root.
	root %s;
	# The cache lifetime.
	add_header Cache-Control: max-age=86400;

	# Handle HTTP error responses.
	error_page 401 /.error/401.html;
	error_page 403 /.error/403.html;
	error_page 404 /.error/404.html;
	location /.error {
		internal;
	}

	# When directories are requested, serve their index.html contents.
	location / {
		if ($request_method = OPTIONS) {
			add_header Allow "OPTIONS, GET";
			return 200;
		}
		index index.html;
		try_files $uri $uri/ =404;
	}
}''' % configuration.www_directory_path  # noqa: E101 W191
            with open(join(configuration.output_directory_path, 'nginx.conf')) as f:  # noqa: E101
                self.assertEquals(expected, f.read())

    def test_post_render_config_with_clean_urls(self):
        self.maxDiff = None

        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Nginx] = {}
            configuration.clean_urls = True
            site = Site(configuration)
            render(site)
            expected = '''server {
	# The port to listen to.
	listen 80;
	# The publicly visible hostname.
	server_name example.com;
	# The path to the local web root.
	root %s;
	# The cache lifetime.
	add_header Cache-Control: max-age=86400;

	# Handle HTTP error responses.
	error_page 401 /.error/401.html;
	error_page 403 /.error/403.html;
	error_page 404 /.error/404.html;
	location /.error {
		internal;
	}

	# Redirect */index.html to their parent directories for clean URLs.
	if ($request_uri ~ "^(.*)/index\.html$") {
		return 301 $1;
	}

	# When directories are requested, serve their index.html contents.
	location / {
		if ($request_method = OPTIONS) {
			add_header Allow "OPTIONS, GET";
			return 200;
		}
		index index.html;
		try_files $uri $uri/ =404;
	}
}''' % configuration.www_directory_path  # noqa: E101 W191
            with open(join(configuration.output_directory_path, 'nginx.conf')) as f:  # noqa: E101
                self.assertEquals(expected, f.read())
