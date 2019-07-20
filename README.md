# Betty 👵

[![Build Status](https://travis-ci.org/bartfeenstra/betty.svg?branch=master)](https://travis-ci.org/bartfeenstra/betty) [![codecov](https://codecov.io/gh/bartfeenstra/betty/branch/master/graph/badge.svg)](https://codecov.io/gh/bartfeenstra/betty)

Betty is a static site generator for [Gramps](https://gramps-project.org/) XML files.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [The command line](#the-command-line)
  - [Configuration files](#configuration-files)
  - [The Python API](#the-python-api)
- [Development](#development)
- [Contributions](#contributions-)

## Features
Betty generates generates a [static site](https://en.wikipedia.org/wiki/Static_web_page) from your genealogy records.
This means that once your site has been generated, you will not need any special software to publish it. It's **fast and
secure**.
- Builds pages for people, places, events, and media.
- Renders interactive maps.
- [Responsive](https://en.wikipedia.org/wiki/Responsive_web_design), and mobile- and touch-friendly interface.
- Privacy and anonymization filters for living people.
- [View an example](https://ancestry.bartfeenstra.com/).

## Installation

### Requirements
- **Python 3.5+**
- Node.js 8+ (optional)

### Instructions
Run `pip install git+https://github.com/bartfeenstra/betty.git`.

## Usage

### The command line
After installation, Betty can be used via the `betty` command:
```
usage: betty [-c CONFIG_FILE_PATH] [-h] ...

Betty is a static ancestry site generator.

positional arguments:
  ...                   The command to run, and any arguments it needs.

optional arguments:
  -c CONFIG_FILE_PATH, --configuration CONFIG_FILE_PATH
                        The path to the configuration file. Defaults to
                        betty.json in the current working directory.
  -h, --help            Show this help message and exit.
```

### Configuration files
Configuration files are written in JSON:
```json
{
	"output": "/var/www/betty",
	"base_url": "https://ancestry.example.com",
	"root_path": "/betty",
	"clean_urls": true,
	"title": "Betty's ancestry",
	"resources": "./resources",
	"plugins": {
		"betty.plugins.anonymizer.Anonymizer": {},
		"betty.plugins.cleaner.Cleaner": {},
		"betty.plugins.gramps.Gramps": {
			"file": "./gramps.gpkg"
		},
		"betty.plugins.maps.Maps": {},
		"betty.plugins.nginx.Nginx": {},
		"betty.plugins.privatizer.Privatizer": {},
		"betty.plugins.wikipedia.Wikipedia": {}
	}
}
```
- `output` (required); The path to the directory in which to place the generated site.
- `base_url` (required); The absolute, public URL at which the site will be published.
- `root_path` (optional); The relative path under the public URL at which the site will be published.
- `clean_urls` (optional); A boolean indicating whether to use clean URLs, e.g. `/path` instead of `/path/index.html`.
- `title` (optional); The site's title.
- `resources` (optional); The path to a directory containing overrides for any of Betty's [resources](./betty/resources).
- `plugins` (optional): The plugins to enable. Keys are plugin names, and values are objects containing each plugin's configuration.
    - `betty.plugin.anonymizer.Anonymizer`: Removes personal information from private people. Configuration: `{}`.
    - `betty.plugin.cleaner.Cleaner`: Removes data (events, media, etc.) that have no relation to any people. Configuration: `{}`.
    - `betty.plugin.gramps.Gramps`: Parses a Gramps genealogy. Configuration:
        - `file`: the path to the *Gramps XML* or *Gramps XML Package* file.
    - `betty.plugin.maps.Maps`: Renders maps using [Leaflet](https://leafletjs.com/).
    - `betty.plugin.nginx.Nginx`: Creates an [nginx](https://nginx.org) configuration file in the output directory . Configuration: `{}`.
    - `betty.plugin.privatizer.Privatizer`: Marks living people private. Configuration: `{}`.
    - `betty.plugin.wikipedia.Wikipedia`: Lets templates and other plugins retrieve complementary Wikipedia entries.

### The Python API
```python
from betty.config import Configuration
from betty.parse import parse
from betty.render import render
from betty.site import Site

output_directory_path = '/var/www/betty'
url = 'https://betty.example.com'
configuration = Configuration(output_directory_path, url)
site = Site(configuration)
parse(site)
render(site)

```

## Development
First, [fork and clone](https://guides.github.com/activities/forking/) the repository, and navigate to its root directory.

### Requirements
- The installation requirements documented earlier.
- Bash (you're all good if `which bash` outputs a path in your terminal)

### Installation
In any existing Python environment, run `./bin/build-dev`.

### Testing
In any existing Python environment, run `./bin/test`.

### Fixing problems automatically
In any existing Python environment, run `./bin/fix`.

## Contributions 🥳
You are welcome to [report bugs](https://github.com/bartfeenstra/betty/issues) or [submit improvements](https://github.com/bartfeenstra/betty/pulls).
