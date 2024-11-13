Asset Management
================

What are assets?
----------------
`Assets <https://en.wikipedia.org/wiki/Digital_asset>`_ are all the **static** files needed for Betty to run or generate
your site, but that are not source code files. Examples of assets:

- imagery
- CSS and JavaScript files
- (Jinja2) templates
- :doc:`translations </usage/translation>`

The assets repository
---------------------

Betty comes with an :py:mod:`Assets API <betty.assets>` that layers the assets provided by all the different components.
Each time an asset is needed, Betty finds it as follows:

#. If the project provides the asset in its assets directory, use it
#. If an extension provides the asset in its assets directory, use it
#. If a built-in translation asset exists, use it (``/betty/assets`` within the Betty source code)

This means that extensions can override Betty's default assets, and your projects can override both extensions'
and Betty's assets.

Assets directories
------------------
For each of Betty's default assets, extensions' assets, and your projects' assets, the assets directory follows the
following structure:

``locale/``
^^^^^^^^^^^^^
Contains assets for different locales.

``locale/betty.pot``
^^^^^^^^^^^^^^^^^^^^^^
The gettext :doc:`translatable message </usage/translation>` catalog.

``locale/$locale/betty.po``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Where ``$locale`` is an `IETF BCP 47 language tag <https://www.ietf.org/rfc/bcp/bcp47.txt>`_, ``betty.po`` is the
gettext :doc:`translations </usage/translation>` file for that locale.

``public/``
^^^^^^^^^^^^^
Contains files that become part of your sites.

``public/localized/``
^^^^^^^^^^^^^^^^^^^^^^^
Contains files that will be localized when generating your sites.

For sites with a single language, this effectively overrides ``public/static`` on a per-file basis.

On multilingual sites, these files end up in a subdirectory based on the locale they are rendered in:
``public/localized/my-page.html.j2`` will be accessible on your site through ``https://example.com/en/my-page.html`` for
an English locale, for example.

Examples of files that should be put here are any files that contain localizable (translatable) content, which will
likely be most, if not all of your HTML pages.

``public/static/``
^^^^^^^^^^^^^^^^^^^^
Contains static files that become part of your sites. ``public/static/my-file.txt`` will be accessible on your site
through ``https://example.com/my-file.txt``.

Examples of files that should often be put here are CSS and JavaScript files, images for your site's look and feel, and
metadata files such as ``robots.txt`` and ``sitemap.xml``.

``templates/``
^^^^^^^^^^^^^^^^
Contains (Jinja2) :doc:`templates </usage/templating>`.
