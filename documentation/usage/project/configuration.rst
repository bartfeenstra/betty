Project configuration
=====================

Project configuration files are written in YAML (``betty.yaml`` or ``betty.yml``) or JSON (``betty.json``)
and are placed in the root of the project directory. Both YAML and JSON files follow the exact same
structure. Example configuration:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          url: https://ancestry.example.com/betty
          debug: true
          clean_urls: true
          title: Betty's ancestry
          name: betty-ancestry
          author: Bart Feenstra
          logo: my-ancestry-logo.png
          lifetime_threshold: 125
          locales:
            - locale: en-US
              alias: en
            - locale: nl
          entity_types:
            person:
              generate_html_list: true
            file:
              generate_html_list: false
          event_types:
            moon-landing:
              label: Moon Landing
          genders:
            genderqueer:
              label: Genderqueer
          place_types:
            moon:
              label: Moon
          presence_roles:
            astronaut:
              label: Astronaut
          extensions: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "url" : "https://ancestry.example.com/betty",
            "debug" : true,
            "clean_urls" : true,
            "title": "Betty's ancestry",
            "name": "betty-ancestry",
            "author": "Bart Feenstra",
            "logo": "my-ancestry-logo.png",
            "lifetime_threshold": 125,
            "locales": [
              {
                "locale": "en-US",
                "alias": "en"
              },
              {
                "locale": "nl"
              }
            ],
            "entity_types": {
              "person": {
                "generate_html_list": true
              },
              "file": {
                "generate_html_list": false
              }
            },
            "event_types": {
              "moon-landing": {
                "label": "Moon Landing"
              }
            },
            "genders": {
              "genderqueer": {
                "label": "Genderqueer"
              }
            },
            "place_types": {
              "moon": {
                "label": "Moon"
              }
            },
            "presence_roles": {
              "astronaut": {
                "label": "Astronaut"
              }
            },
            "extensions": {}
          }

All configuration options
-------------------------

- ``url`` (required): The absolute, public URL at which the site will be published.
- ``debug`` (optional): ``true`` to output more detailed logs and disable optimizations that make debugging harder. Defaults to ``false``.
- ``clean_urls`` (optional): A boolean indicating whether to use clean URLs, e.g. ``/path`` instead of ``/path/index.html``. Defaults to ``false``.
- ``title`` (optional): The project's human-readable title. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
- ``name`` (optional): The project's machine name.
- ``author`` (optional): The project's author and copyright holder. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
- ``logo`` (optional): The path to your site's logo file. Defaults to the Betty logo.
- ``lifetime_threshold`` (optional); The number of years people are expected to live at most, e.g. after which they're presumed to have died. Defaults to ``125``.
- ``locales`` (optional); An array of locales, each of which is an object with the following keys:

  - ``locale`` (required): An `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
  - ``alias`` (optional): A shorthand alias to use instead of the full language tag, such as when rendering URLs.

  If no locales are specified, Betty defaults to US English (``en-US``). Read more about :doc:`translations </usage/translation>`.
- ``entity_types`` (optional): Keys are entity type (plugin) IDs, and values are objects containing the following keys:

  - ``generate_html_list`` (optional): Whether to generate the HTML page to list entities of this type. Defaults to ``false``.
- ``event_types`` (optional): Keys are event type (plugin) IDs, and values are objects containing the following keys:

  - ``label`` (required): The event type's human-readable label. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
  - ``description`` (optional): The event type's human-readable long description. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
- ``genders`` (optional): Keys are gender (plugin) IDs, and values are objects containing the following keys:

  - ``label`` (required): The gender's human-readable label. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
  - ``description`` (optional): The gender's human-readable long description. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
- ``place_types`` (optional): Keys are place type (plugin) IDs, and values are objects containing the following keys:

  - ``label`` (required): The place type's human-readable label. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
  - ``description`` (optional): The place type's human-readable long description. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
- ``presence_roles`` (optional): Keys are presence role (plugin) IDs, and values are objects containing the following keys:

  - ``label`` (required): The presence role's human-readable label. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
  - ``description`` (optional): The presence role's human-readable long description. This can be a string or :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
- ``extensions`` (optional): The :doc:`extensions </usage/extension>` to enable. Keys are extension names, and values are objects containing the
  following keys:

  - ``enabled`` (optional): A boolean indicating whether the extension is enabled. Defaults to ``true``.
  - ``configuration`` (optional): An object containing the extension's own configuration, if it provides any configuration options.

  Both keys may be omitted to quickly enable an extension using its default configuration.
