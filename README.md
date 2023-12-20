# Betty 👵

![Test status](https://github.com/bartfeenstra/betty/workflows/Test/badge.svg?branch=0.3.x) [![Code coverage](https://codecov.io/gh/bartfeenstra/betty/branch/0.3.x/graph/badge.svg)](https://codecov.io/gh/bartfeenstra/betty) [![PyPI releases](https://badge.fury.io/py/betty.svg)](https://pypi.org/project/betty/) [![Supported Python versions](https://img.shields.io/pypi/pyversions/betty.svg?logo=python&logoColor=FBE072)](https://pypi.org/project/betty/) [![Recent downloads](https://img.shields.io/pypi/dm/betty.svg)](https://pypi.org/project/betty/) [![Follow Betty on Twitter](https://img.shields.io/twitter/follow/Betty_Project.svg?label=Betty_Project&style=flat&logo=twitter&logoColor=4FADFF)](https://twitter.com/Betty_Project)

Betty helps you visualize and publish your family history by building interactive genealogy websites out of your
[Gramps](https://gramps-project.org/) and [GEDCOM](https://en.wikipedia.org/wiki/GEDCOM) family trees.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [The command line](#the-command-line)
  - [The desktop application](#the-desktop-application)
  - [Projects](#projects)
    - [Project configuration files](#project-configuration-files)
  - [Application configuration file](#application-configuration-file)
  - [Translations](#translations)
  - [Gramps](#gramps)
  - [GEDCOM files](#gedcom-files)
  - [The Python API](#the-python-api)
- [Development](#development)
- [Contributions](#contributions-)
- [Copyright & license](#copyright--license)

## Features

Betty generates [static sites](https://en.wikipedia.org/wiki/Static_web_page) from your genealogy records.
This means that once your site has been generated, you will not need any special software to publish it. It's **fast and
secure**.

- Builds pages for people, places, events, and media.
- Renders interactive maps.
- Fully multilingual: localize the site to one or more languages of your choice.
- [Responsive](https://en.wikipedia.org/wiki/Responsive_web_design), and mobile- and touch-friendly interface.
- Privatization filters for living people.
- [View an example](https://ancestry.bartfeenstra.com/).

## Installation

### Requirements

Linux, Mac OS, or Windows.

### Install the desktop application
For Mac OS, [download](https://github.com/bartfeenstra/betty/releases) `betty.app.zip`.

For Windows, [download](https://github.com/bartfeenstra/betty/releases) `betty.exe.zip`.

### Install via pip

#### Requirements

- **Python 3.11+**
- [Node.js](https://nodejs.org/) (optional)

#### Instructions

Run `pip install betty` to install the latest stable release.

To install the latest development version, run `pip install git+https://github.com/bartfeenstra/betty.git`. If you want
the latest source code, read the [development](#development) documentation.

## Usage

### The command line

After installation, Betty can be used via the `betty` command:

```
Usage: betty [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --configuration TEXT  The path to a Betty project configuration file.
                            Defaults to betty.json|yaml|yml in the current
                            working directory. This will make additional
                            commands available.
  --version                 Show the version and exit.
  --help                    Show this message and exit.

Commands:
  clear-caches         Clear all caches.
  demo                 Explore a demonstration site.
  gui                  Open Betty's graphical user interface (GUI).
  init-translation     Initialize a new translation
  update-translations  Update all existing translations
  generate             Generate a static site.
  serve                Serve a generated site.
```

### The desktop application

You can [download](https://github.com/bartfeenstra/betty/releases) Betty as Mac OS and Windows
desktop applications.

If you have installed Betty as a command line application, run `betty gui` to launch the desktop
application.

### Projects

A project contains all the information necessary to turn a family tree into a site. After installing 
Betty once, you can manage multiple projects.

You can create and tailer projects through the Betty desktop application, or through the command 
line using configuration files.

#### Project configuration files

Project configuration files are written in YAML (`betty.yaml` or `betty.yml`) or JSON (`betty.json`)
and are placed in the root of the project directory. Both YAML and JSON files follow the exact same
structure. An example YAML configuration:

```yaml
base_url: https://ancestry.example.com
debug: true
root_path: /betty
clean_urls: true
title: Betty's ancestry
author: Bart Feenstra
lifetime_threshold: 125
locales:
  en-US:
    alias: en
  nl: {}
entity_types:
  Person:
    generate_html_list: true
  File:
    generate_html_list: false
extensions:
  betty.extension.CottonCandy:
    configuration:
      primary_inactive_color: '#ffc0cb'
      primary_active_color: '#ff69b4'
      link_inactive_color: '#149988'
      link_active_color: '#2a615a'
      featured_entities:
        - entity_type: Person
          entity_id: P123
        - entity_type: Place
          entity_id: Amsterdam
  betty.extension.Deriver: {}
  betty.extension.Gramps:
    configuration:
      family_trees:
        - file: ./gramps.gpkg
  betty.extension.HttpApiDoc: {}
  betty.extension.Maps: {}
  betty.extension.Nginx:
    configuration:
      https: true
      www_directory_path: /var/www/betty
  betty.extension.Privatizer: {}
  betty.extension.Trees: {}
  betty.extension.Wikipedia: {}
```

- `base_url` (required): The absolute, public URL at which the site will be published.
- `debug` (optional): `true` to output more detailed logs and disable optimizations that make debugging harder. Defaults
  to `false`.
- `root_path` (optional): The relative path under the public URL at which the site will be published.
- `clean_urls` (optional): A boolean indicating whether to use clean URLs, e.g. `/path` instead of `/path/index.html`.
  Defaults to `false`.
- `content_negotiation` (optional): Enables dynamic content negotiation, but requires a web server
  that supports it. This implies `clean_urls`. Defaults to `false`
- `title` (optional): The project's title.
- `author` (optional): The project's author and copyright holder.
- `lifetime_threshold` (optional); The number of years people are expected to live at most, e.g. after which they're
  presumed to have died. Defaults to `125`.
- `locales` (optional); An array of locales, each of which is an object with the following keys:
  - `locale`(required): An [IETF BCP 47](https://tools.ietf.org/html/bcp47) language tag.
  - `alias` (optional): A shorthand alias to use instead of the full language tag, such as when rendering URLs.

  If no locales are specified, Betty defaults to US English.
- `entity_types` (optional): Keys are entity type names, and values are objects containing the following keys:
  - `generate_html_list` (optional): Whether to generate the HTML page to list entities of this type. Defaults to
    `false`.
- `extensions` (optional): The extensions to enable. Keys are extension names, and values are objects containing the
  following keys:
  - `enabled` (optional): A boolean indicating whether the extension is enabled. Defaults to `true`.
  - `configuration` (optional): An object containing the extension's own configuration, if it provides any configuration
    options.

  Both keys may be omitted to quickly enable an extension using its default configuration.

  The extensions that ship with Betty, and their configuration:
  - `betty.extension.CottonCandy` (optional): Configuration:
    - `primary_inactive_color` (optional): The case-insensitive hexadecimal code for the primary color. Defaults to
      `#ffc0cb`.
    - `primary_active_color` (optional): The case-insensitive hexadecimal code for the primary color for actively
      engaged elements. Defaults to `#ff69b4`.
    - `link_inactive_color` (optional): The case-insensitive hexadecimal code for the link color. Defaults to `#149988`.
    - `link_active_color` (optional): The case-insensitive hexadecimal code for the color of actively engaged links.
      Defaults to `#2a615a`.
    - `featured_entities` (optional): A list of entities to feature on the front page. Each item has the following
      configuration:
      - `entity_type` (required): The name of the entity type to feature, e.g. `Person`.
      - `entity_id` (required):  The ID of the entity type to feature, e.g. `P123`.
    provides no configuration options.
  - `betty.extension.Demo` (optional): Loads demonstrative content and functionality that shows what Betty can do. It
    provides no configuration options.
  - `betty.extension.Deriver` (optional): Extends ancestries by deriving facts from existing information. It provides no
    configuration options.
  - `betty.extension.Gramps` (optional): Loads Gramps family trees. Configuration:
    - `family_trees` (required): An array defining zero or more Gramps family trees to load. Each item is an object with
      the following keys:
      - `file` (required): the path to a *Gramps XML* or *Gramps XML Package* file.
  - `betty.extension.HttpApiDoc` (optional): Renders interactive and user-friendly HTTP API documentation
    using [ReDoc](https://github.com/Redocly/redoc).
  - `betty.extension.Maps` (optional): Renders interactive maps using [Leaflet](https://leafletjs.com/).
  - `betty.extension.Nginx` (optional): Generates a [nginx](https://nginx.org) configuration file for your project's site,
    and the ability to serve your site using nginx and [Docker](https://www.docker.com/) (requires Docker to be installed
    on your system).

    The Docker image does not currently support secure connections ([read more](https://github.com/bartfeenstra/betty/issues/1056)).
    For HTTPS support, you will have to set up a separate web server to terminate SSL, and forward all traffic to the container over HTTP.

    Configuration:
    - `https` (optional): A boolean to enforce HTTPS in the nginx configuration.
     Defaults to whether the project's base URL uses HTTPS.
    - `www_directory_path` (optional): A string to override the WWW directory path in the nginx configuration.
     Defaults to the project's WWW directory path.
  - `betty.extension.Privatizer` (optional): Marks living people private. Configuration: `{}`.
  - `betty.extension.Trees` (optional): Renders interactive ancestry trees using [Cytoscape.js](http://js.cytoscape.org/).
  - `betty.extension.Wikipedia` (optional): Lets templates and other extensions retrieve complementary Wikipedia
    entries.

### Application configuration file

Betty also uses global application configuration for settings that do not impact your projects, such
as the language you want to use Betty in, e.g. for the desktop application and logs. This configuration
can be managed through the desktop application as well as through a configuration file.

The application configuration file is written in JSON and placed at `$HOME/.betty/configuration/app.json`.
An example configuration:

```json
{
  "locale": "nl-NL"
}
```

- `locale` (optional): An [IETF BCP 47](https://tools.ietf.org/html/bcp47) language tag.
  If no locale is specified, Betty defaults to US English. 

### Translations

Betty ships with the following translations:

- US English (`en-US`)
- Dutch (`nl-NL`)
- French (`fr-FR`)
- Ukrainian (`uk`)

Extensions and projects can override these translations, or provide translations for additional locales.

### Gramps

#### Privacy

Gramps has limited built-in support for people's privacy. To fully control privacy for people, as well as events, files,
sources, and citations, add a `betty:privacy` attribute to any of these types, with a value of `private` to explicitly
declare the data always private or `public` to declare the data always public. Any other value will leave the privacy
undecided, as well as person records marked public using Gramps' built-in privacy selector. In such cases, the
`betty.extension.Privatizer` extension may decide if the data is public or private.

#### Dates

For unknown date parts, set those to all zeroes and Betty will ignore them. For instance, `0000-12-31` will be parsed as
"December 31", and `1970-01-00` as "January, 1970".

#### Event types

Betty supports the following Gramps event types:

- `Adopted`
- `Birth`
- `Burial`
- `Baptism`
- `Conference`
- `Confirmation`
- `Correspondence`
- `Cremation`
- `Emigration`
- `Engagement`
- `Death`
- `Divorce`
- `Divorce Filing` (imported as `DivorceAnnouncement`)
- `Funeral`
- `Immigration`
- `Marriage`
- `Marriage Banns` (imported as `MarriageAnnouncement`)
- `Missing`
- `Occupation`
- `Residence`
- `Will`
- `Retirement`

#### Event roles

Betty supports the following Gramps event roles:

- `Attendee`
- `Beneficiary`
- `Celebrant`
- `Family` (imported as `Subject`)
- `Organizer`
- `Primary` (imported as `Subject`)
- `Speaker`
- `Unknown` (imported as `Attendee`)
- `Witness`

#### Order & priority

The order of lists of data, or the priority of individual bits of data, can be automatically determined by Betty in
multiple different ways, such as by matching dates, or locales. When not enough details are available, or in case of
ambiguity, the original order is preserved. If only a single item must be retrieved from the list, this will be the
first item, optionally after sorting.

For example, if a place has multiple names (which may be historical or translations), Betty may try to
filter names by the given locale and date, and then indiscriminately pick the first one of the remaining names to
display as the canonical name.

Tips:

- If you want one item to have priority over another, it should come before the other in a list (e.g. be higher up).
- Items with more specific or complete data, such as locales or dates, should come before items with less specific or
  complete data. However, items without dates at all are considered current and not historical.
- Unofficial names or nicknames, should generally be put at the end of lists.

### GEDCOM files

To build a site from your GEDCOM files:

1. Install and launch [Gramps](https://gramps-project.org/)
1. Create a new family tree
1. Import your GEDCOM file under *Family Trees* > *Import...*
1. Export your family tree under *Family Trees* > *Export...*
1. As output format, choose one of the *Gramps XML* options
1. Follow the documentation to [configure your Betty site](#configuration-files) to load the exported file

### The Python API

```python
from betty.app import App
from betty.asyncio import sync
from betty.generate import generate
from betty.load import load


@sync
async def generate():
    async with App() as app:
        await load(app)
        await generate(app)

```

### Environment variables
- `BETTY_CONCURRENCY`: The concurrency factor expressed as an integer. Defaults to the number of CPU cores. Set to `1`
  to disable concurrency altogether. Example: `BETTY_CONCURRENCY=4`. 

## Development

First, [fork and clone](https://guides.github.com/activities/forking/) the repository, and navigate to its root
directory.

### Requirements

- **Python 3.11+**
- [Node.js](https://nodejs.org/)
- [ShellCheck](https://www.shellcheck.net/)
- [Xvfb](https://x.org/releases/X11R7.7/doc/man/man1/Xvfb.1.xhtml)
- The Cypress 
  [system requirements](https://docs.cypress.io/guides/getting-started/installing-cypress#System-requirements) and 
  [individual packages](https://docs.cypress.io/guides/continuous-integration/introduction#Dependencies) (headless Linux
 only)
- Bash

### Installation

In any existing Python environment, run `./bin/build-dev`.

### Working on translations

#### Making changes to the translatable strings in the source code

Run `betty update-translations` to update the translations files with the changes you made.

#### Adding translations for a language for which no translations exist yet

Run `betty init-translation $locale` where `$locale` is an
[IETF BCP 47 language tag](https://tools.ietf.org/html/bcp47).

#### Updating the translations for a language

First, install a PO file editor on your system. Any will do, but if you don't want to search for one,
[Poedit](https://poedit.net/) is a good and free editor to start with.

Then, with this PO file editor, open and change the `*.po` file for the translations you want to change. For Dutch
(Netherlands), that is [`./betty/assets/locale/nl-NL/betty.po`](betty/assets/locale/nl-NL/betty.po), for example.

### Testing

In any existing Python environment, run `./bin/test`.

#### Environment variables
These impact the `./bin/test` command:
- `BETTY_TEST_SKIP_SHELLCHECK=true`: Skip ShellCheck tests.
- `BETTY_TEST_SKIP_FLAKE8=true`: Skip Flake8 tests.
- `BETTY_TEST_SKIP_MYPY=true`: Skip mypy tests.
- `BETTY_TEST_SKIP_STYLELINT=true`: Skip Stylelint tests.
- `BETTY_TEST_SKIP_ESLINT=true`: Skip ESLint tests.
- `BETTY_TEST_SKIP_CYPRESS=true`: Skip Cypress tests.
- `BETTY_TEST_SKIP_PYINSTALLER=true`: Skip the PyInstaller test build.

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
