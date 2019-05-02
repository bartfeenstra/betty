# Betty

[![Build Status](https://travis-ci.org/bartfeenstra/betty.svg?branch=master)](https://travis-ci.org/bartfeenstra/betty) [![codecov](https://codecov.io/gh/bartfeenstra/betty/branch/master/graph/badge.svg)](https://codecov.io/gh/bartfeenstra/betty)

Betty is a static site generator for [Gramps](https://gramps-project.org/) XML files.

## Usage

### Requirements
- Python 3.5+

### Installation
- Clone the repository.
- Inside the Betty project directory, run `pip install .`.

### The command line
After installation, Betty can be used via the `betty` command:
```
usage: betty [-h] {generate} ...

Betty is a static ancestry site generator.

positional arguments:
  {generate}

optional arguments:
  -h, --help  show this help message and exit
```

### Nginx configuration
To serve the generated site with nginx, you can alter and use the following configuration:
```
server {
	# The port to listen to.
	listen 80;
	# The publicly visible hostname.
	server_name $publicHostname;
	# The path to the local web root.
	root $localWebRoot;
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
		index index.html;
		try_files $uri $uri/ =404;
	}
}
```

## Development
First, clone the repository, and navigate to its root directory.

### Requirements
- The usage requirements documented earlier.
- Bash (you're all good if `which bash` outputs a path in your terminal)

### Installation
In any existing Python environment, run `./bin/build-dev`.

Or with tox, run `tox --develop --notest`.

### Testing
In any existing Python environment, run `./bin/test`.

Or with tox, run `tox`. 

### Fixing problems automatically
In any existing Python environment, run `./bin/fix`.
