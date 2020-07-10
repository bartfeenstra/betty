# Betty 👵

[![Build Status](https://travis-ci.org/bartfeenstra/betty.svg?branch=master)](https://travis-ci.org/bartfeenstra/betty) [![codecov](https://codecov.io/gh/bartfeenstra/betty/branch/master/graph/badge.svg)](https://codecov.io/gh/bartfeenstra/betty)

Betty is a static site generator for [Gramps](https://gramps-project.org/) and
[GEDCOM](https://en.wikipedia.org/wiki/GEDCOM) family trees.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [The command line](#the-command-line)
  - [Configuration files](#configuration-files)
  - [Translations](#translations)
  - [Gramps](#gramps)
  - [GEDCOM files](#gedcom-files)
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
- **Python 3.6+**
- Node.js 10+ (optional)

### Instructions
Run `pip install git+https://github.com/bartfeenstra/betty.git`.

## Usage

### The command line
After installation, Betty can be used via the `betty` command:
```
Usage: betty [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --configuration TEXT  The path to a Betty site configuration file.
                            Defaults to betty.json|yaml|yml in the current
                            working directory. This will make additional
                            commands available.

  --help                    Show this message and exit.

Commands:
  clear-caches  Clear all caches.
  generate      Generate a static site.
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
assets_directory_path: ./resources
plugins:
  betty.plugin.anonymizer.Anonymizer: ~
  betty.plugin.cleaner.Cleaner: ~
  betty.plugin.deriver.Deriver: ~
  betty.plugin.gramps.Gramps:
    file: ./gramps.gpkg
  betty.plugin.maps.Maps: ~
  betty.plugin.nginx.Nginx:
    www_directory_path: /var/www/betty
    https: true
  betty.plugin.privatizer.Privatizer: ~
  betty.plugin.trees.Trees: ~
  betty.plugin.wikipedia.Wikipedia: ~
```
- `output` (required); The path to the directory in which to place the generated site.
- `base_url` (required); The absolute, public URL at which the site will be published.
- `root_path` (optional); The relative path under the public URL at which the site will be published.
- `clean_urls` (optional); A boolean indicating whether to use clean URLs, e.g. `/path` instead of `/path/index.html`.
- `content_negotiation` (optional, defaults to `false`): Enables dynamic content negotiation, but requires a web server
    that supports it. Also see the `betty.plugin.nginx.Nginx` plugin. This implies `clean_urls`.
- `title` (optional); The site's title.
- `author` (optional); The site's author and copyright holder.
- `locales` (optional); An array of locales, each of which is an object with the following keys:
    - `locale`(required): An [IETF BCP 47](https://tools.ietf.org/html/bcp47) language tag.
    - `alias` (optional): A shorthand alias to use instead of the full language tag, such as when rendering URLs.

    If no locales are defined, Betty defaults to US English.
- `assets_directory_path` (optional); The path to a directory containing overrides for any of Betty's
    [assets](./betty/assets).
- `plugins` (optional): The plugins to enable. Keys are plugin names, and values are objects containing each plugin's configuration.
    - `betty.plugin.anonymizer.Anonymizer`: Removes personal information from private people. Configuration: `~`.
    - `betty.plugin.cleaner.Cleaner`: Removes data (events, media, etc.) that have no relation to any people. Configuration: `~`.
    - `betty.plugin.deriver.Deriver`: Extends ancestries by deriving facts from existing information. Configuration: `~`.
    - `betty.plugin.gramps.Gramps`: Parses a Gramps genealogy. Configuration:
        - `file`: the path to the *Gramps XML* or *Gramps XML Package* file.
    - `betty.plugin.maps.Maps`: Renders interactive maps using [Leaflet](https://leafletjs.com/).
    - `betty.plugin.nginx.Nginx`: Creates an [nginx](https://nginx.org) configuration file in the output directory.
        If `content_negotiation` is enabled. You must make sure the nginx
        [Lua module](https://github.com/openresty/lua-nginx-module#readme) is enabled, and
        [CONE](https://github.com/bartfeenstra/cone)'s
        [cone.lua](https://raw.githubusercontent.com/bartfeenstra/cone/master/cone.lua) can be found by putting it in
        nginx's [lua_package_path](https://github.com/openresty/lua-nginx-module#lua_package_path). Configuration:
        - `www_directory_path` (optional): The public www directory where Betty will be deployed. Defaults to `www`
            inside the output directory.
        - `https` (optional): Whether or not nginx will be serving Betty over HTTPS. Most upstream nginx servers will
            want to have this disabled, so the downstream server can terminate SSL and communicate over HTTP 2 instead.
            Defaults to `true` if the base URL specifies HTTPS, or `false` otherwise.
    - `betty.plugin.privatizer.Privatizer`: Marks living people private. Configuration: `~`.
    - `betty.plugin.trees.Trees`: Renders interactive ancestry trees using [Cytoscape.js](http://js.cytoscape.org/).
    - `betty.plugin.wikipedia.Wikipedia`: Lets templates and other plugins retrieve complementary Wikipedia entries.

### Translations
Betty ships with the following translations:
- US English (`en-US`)
- Dutch (`nl-NL`)
- Ukrainian (`uk`)

Plugins and sites can override these translations, or provide translations for additional locales.

### Gramps
#### Privacy
Gramps has limited built-in support for people's privacy. To fully control privacy for people, as well as events, files,
sources, and citations, add a `betty:privacy` attribute to any of these types, with a value of `private` to explicitly
declare the data always private or `public` to declare the data always public. Any other value will leave the privacy
undecided, as well as person records marked public using Gramps' built-in privacy selector. In such cases, the
`betty.plugin.privatizer.Privatizer` may decide if the data is public or private.

#### Dates
For unknown date parts, set those to all zeroes and Betty will ignore them. For instance, `0000-12-31` will be parsed as
"December 31", and `1970-01-00` as "January, 1970".

#### Event types
Betty supports the following custom Gramps event types:
- `Correspondence`
- `Funeral`
- `Will`

#### Event roles
Betty supports the following custom Gramps event roles:
- `Beneficiary`

### GEDCOM files
To build a site from your GEDCOM files:
1. Install and launch [Gramps](https://gramps-project.org/)
1. Create a new family tree
1. Import your GEDCOM file under *Family Trees* > *Import...*
1. Export your family tree under *Family Trees* > *Export...*
1. As output format, choose one of the *Gramps XML* options
1. Follow the documentation to [configure your Betty site](#configuration-files) to parse the exported file

### The Python API
```python
from betty.config import Configuration
from betty.functools import sync
from betty.generate import generate
from betty.parse import parse
from betty.site import Site

@sync
async def generate():
    output_directory_path = '/var/www/betty'
    url = 'https://betty.example.com'
    configuration = Configuration(output_directory_path, url)
    async with Site(configuration) as site:
        await parse(site)
        await generate(site)

```

## Development
First, [fork and clone](https://guides.github.com/activities/forking/) the repository, and navigate to its root directory.

### Requirements
- The installation requirements documented earlier.
- Node.js
- [Docker](https://www.docker.com/)
- Bash (you're all good if `which bash` outputs a path in your terminal)

### Installation
In any existing Python environment, run `./bin/build-dev`.

### Working on translations
To add a new translation, run `./bin/init-translation $locale` where `$locale` is a
[IETF BCP 47](https://tools.ietf.org/html/bcp47), but using underscores instead of dashes (`nl_NL` instead of `nl-NL`).

After making changes to the translatable strings in the source code, run `./bin/extract-translatables`.

After making changes to the translation files, run `./bin/compile-translatables`.

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
