Configuration
=============

Configuration files are written in YAML (``*.yaml`` or ``*.yml``) or JSON (``*.json``):

.. code-block:: yaml

    output: /var/www/betty
    base_url: https://ancestry.example.com
    root_path: /betty
    clean_urls: true
    title: Betty's ancestry
    author: Bart Feenstra
    lifetime_threshold: 125
    locales:
      - locale: en-US
        alias: en
      - locale: nl
    assets_directory_path: ./resources
    extensions: {}

* ``output`` (required): The path to the directory in which to place the generated site.
* ``base_url`` (required): The absolute, public URL at which the site will be published.
* ``root_path`` (optional): The relative path under the public URL at which the site will be published.
* ``clean_urls`` (optional): A boolean indicating whether to use clean URLs, e.g. ``/path`` instead of
  ``/path/index.html``.
* ``content_negotiation`` (optional, defaults to ``false``): Enables dynamic content negotiation, but requires a web
  server that supports it. Also see the ``betty.extension.nginx.Nginx`` extension. This implies ``clean_urls``.
* ``title`` (optional): The site's title.
* ``author`` (optional): The site's author and copyright holder.
* ``lifetime_threshold`` (optional): The number of years people are expected to live at most, e.g. after which they're
  presumed to have died. Defaults to ``125``.
* ``locales`` (optional): An array of locales, each of which is an object with the following keys:

  * ``locale`` (required): An `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
  * ``alias`` (optional): A shorthand alias to use instead of the full language tag, such as when rendering URLs.

  If no locales are defined, Betty defaults to US English.
* ``assets_directory_path`` (optional): The path to a directory containing overrides for any of Betty's assets, such as
  templates and translations.
* ``extensions`` (optional): The extensions to enable. Keys are extension names, and values are objects containing each
  extension's configuration. Explore :ref:`Betty's built-in extensions <extension-builtin>`.
