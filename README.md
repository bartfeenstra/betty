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
- [Contributions](#contributions)
- [License](#license)

## Features
Betty generates generates a [static site](https://en.wikipedia.org/wiki/Static_web_page) from your genealogy records.
This means that once your site has been generated, you will not need any special software to publish it. It's **fast and
secure**.
- Builds pages for people, places, events, and media.
- Renders interactive maps.
- Fully multilingual: localize the site to one or more languages of your choice.
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
Configuration files are written in YAML (`*.yaml` or `*.yml`) or JSON (`*.json`):
```yaml
output: /var/www/betty
base_url: https://ancestry.example.com
root_path: /betty
clean_urls: true
title: Betty's ancestry
author: Bart Feenstra
locales:
  - locale: en-US
    alias: en
  - locale: nl
resources: ./resources
plugins:
  betty.plugins.anonymizer.Anonymizer: {}
  betty.plugins.cleaner.Cleaner: {}
  betty.plugins.gramps.Gramps:
    file: ./gramps.gpkg
  betty.plugins.maps.Maps: {}
  betty.plugins.nginx.Nginx:
    content_negotiation: true
  betty.plugins.privatizer.Privatizer: {}
  betty.plugins.search.Search: {}
  betty.plugins.trees.Trees: {}
  betty.plugins.wikipedia.Wikipedia: {}
```
- `output` (required); The path to the directory in which to place the generated site.
- `base_url` (required); The absolute, public URL at which the site will be published.
- `root_path` (optional); The relative path under the public URL at which the site will be published.
- `clean_urls` (optional); A boolean indicating whether to use clean URLs, e.g. `/path` instead of `/path/index.html`.
- `content_negotiation` (optional, defaults to `false`): Enables dynamic content negotiation, but requires a web server
    that supports it. Also see the `betty.plugins.nginx.Nginx` plugin. This implies `clean_urls`.
- `title` (optional); The site's title.
- `author` (optional); The site's author and copyright holder.
- `locales` (optional); An array of locales, each of which is an object with the following keys:
    - `locale`(required): An [IETF BCP 47](https://tools.ietf.org/html/bcp47) language tag.
    - `alias` (optional): A shorthand alias to use instead of the full language tag, such as when rendering URLs.

    If no locales are defined, Betty defaults to US English.
- `resources` (optional); The path to a directory containing overrides for any of Betty's [resources](./betty/resources).
- `plugins` (optional): The plugins to enable. Keys are plugin names, and values are objects containing each plugin's configuration.
    - `betty.plugin.anonymizer.Anonymizer`: Removes personal information from private people. Configuration: `{}`.
    - `betty.plugin.cleaner.Cleaner`: Removes data (events, media, etc.) that have no relation to any people. Configuration: `{}`.
    - `betty.plugin.gramps.Gramps`: Parses a Gramps genealogy. Configuration:
        - `file`: the path to the *Gramps XML* or *Gramps XML Package* file.
    - `betty.plugin.maps.Maps`: Renders interactive maps using [Leaflet](https://leafletjs.com/).
    - `betty.plugin.nginx.Nginx`: Creates an [nginx](https://nginx.org) configuration file in the output directory.
        Configuration: `{}`. If `content_negotiation` is enabled. You must make sure the nginx
        [Lua module](https://github.com/openresty/lua-nginx-module#readme) is enabled, and
        [CONE](https://github.com/bartfeenstra/cone)'s
        [cone.lua](https://raw.githubusercontent.com/bartfeenstra/cone/master/cone.lua) can be found by putting it in
        nginx's [lua_package_path](https://github.com/openresty/lua-nginx-module#lua_package_path).
    - `betty.plugin.privatizer.Privatizer`: Marks living people private. Configuration: `{}`.
    - `betty.plugin.search.Search`: Allows users to search through content.
    - `betty.plugin.trees.Trees`: Renders interactive ancestry trees using [Cytoscape.js](http://js.cytoscape.org/).
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
- [Docker](https://www.docker.com/)
- [jq](https://stedolan.github.io/jq/)
- Bash (you're all good if `which bash` outputs a path in your terminal)

### Installation
In any existing Python environment, run `./bin/build-dev`.

### Testing
In any existing Python environment, run `./bin/test`.

### Fixing problems automatically
In any existing Python environment, run `./bin/fix`.

## Contributions 🥳
Betty is Free and Open Source Software. As such you are welcome to
[report bugs](https://github.com/bartfeenstra/betty/issues) or
[submit improvements](https://github.com/bartfeenstra/betty/pulls).

## Copyright & license
Betty is copyright [Bart Feenstra](https://twitter.com/BartFeenstra/) and contributors, and released under the
[GNU General Public License, Version 3](./LICENSE.txt). In short, that means **you are free to use Betty**, but **if you
distribute Betty yourself, you must do so under the exact same license**, provide that license, and make your source
code available. 
