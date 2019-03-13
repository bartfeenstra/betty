# Betty

[![Build Status](https://travis-ci.org/bartfeenstra/betty.svg?branch=master)](https://travis-ci.org/bartfeenstra/betty)

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

	error_page 401 /.error/401.html;
	error_page 403 /.error/403.html;
	error_page 404 /.error/404.html;
	location /.error {
		internal;
	}
	location / {
		index index.html;
		try_files $uri $uri/ =404;
	}
}

```
