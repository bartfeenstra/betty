Project configuration
=====================

Project configuration files are written in YAML (``betty.yaml`` or ``betty.yml``) or JSON (``betty.json``)
and are placed in the root of the project directory. Both YAML and JSON files follow the exact same
structure. Example configuration:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          base_url: https://ancestry.example.com
          debug: true
          root_path: /betty
          clean_urls: true
          title: Betty's ancestry
          name: betty-ancestry
          author: Bart Feenstra
          lifetime_threshold: 125
          locales:
            en-US:
              alias: en
            nl: {}
          entity_types:
            person:
              generate_html_list: true
            file:
              generate_html_list: false
          extensions: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "base_url" : "https://ancestry.example.com",
            "debug" : true,
            "root_path" : "/betty",
            "clean_urls" : true,
            "title": "Betty's ancestry",
            "name": "betty-ancestry",
            "author": "Bart Feenstra",
            "lifetime_threshold": 125,
            "locales": {
              "en-US": {
                "alias": "en"
              },
              "nl": {}
            },
            "entity_types": {
              "person": {
                "generate_html_list": true
              },
              "file": {
                "generate_html_list": false
              }
            },
            "extensions": {}
          }

All configuration options
-------------------------

- ``base_url`` (required): The absolute, public URL at which the site will be published.
- ``debug`` (optional): ``true`` to output more detailed logs and disable optimizations that make debugging harder. Defaults to ``false``.
- ``root_path`` (optional): The relative path under the public URL at which the site will be published.
- ``clean_urls`` (optional): A boolean indicating whether to use clean URLs, e.g. ``/path`` instead of ``/path/index.html``. Defaults to ``false``.
- ``title`` (optional): The project's human-readable title.
- ``name`` (optional): The project's machine name.
- ``author`` (optional): The project's author and copyright holder.
- ``lifetime_threshold`` (optional); The number of years people are expected to live at most, e.g. after which they're presumed to have died. Defaults to ``125``.
- ``locales`` (optional); An array of locales, each of which is an object with the following keys:

  - ``locale`` (required): An `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
  - ``alias`` (optional): A shorthand alias to use instead of the full language tag, such as when rendering URLs.

  If no locales are specified, Betty defaults to US English (``en-US``). Read more about :doc:`translations </usage/translation>`.
- ``entity_types`` (optional): Keys are entity type (plugin) IDs, and values are objects containing the following keys:

  - ``generate_html_list`` (optional): Whether to generate the HTML page to list entities of this type. Defaults to ``false``.
- ``extensions`` (optional): The :doc:`extensions </usage/extension>` to enable. Keys are extension names, and values are objects containing the
  following keys:

  - ``enabled`` (optional): A boolean indicating whether the extension is enabled. Defaults to ``true``.
  - ``configuration`` (optional): An object containing the extension's own configuration, if it provides any configuration options.

  Both keys may be omitted to quickly enable an extension using its default configuration.
