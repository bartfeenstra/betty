# Betty

[![Build Status](https://travis-ci.org/bartfeenstra/betty.svg?branch=master)](https://travis-ci.org/bartfeenstra/betty) [![codecov](https://codecov.io/gh/bartfeenstra/betty/branch/master/graph/badge.svg)](https://codecov.io/gh/bartfeenstra/betty)

Betty is a static site generator for [Gramps](https://gramps-project.org/) XML files.

## Usage

### Nginx configuration
```
server {
	# The port to listen to.
	listen 80;
	# The publicly visible hostname.
	server_name $publicHostname;
	# The path to the local web root.
	root $localWebRoot;

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
		index index.html;
		try_files $uri $uri/ =404;
	}
}
```
