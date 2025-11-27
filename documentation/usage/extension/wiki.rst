The *Wiki* extension
====================
The ``wikip`` extension enriches your ancestry and site with content from Wikipedia and Wikimedia Commons.

Enable this extension in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            wiki: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "wiki": {}
            }
          }

Configuration
-------------
This extension is configurable:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            wiki:
              configuration:
                populate_images: false

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "wiki": {
                "configuration" : {
                  "populate_images": false
                }
              }
            }
          }


``populate_images``
^^^^^^^^^^^^^^^^^^^
:sup:`optional`

A boolean indicating whether to download images from the Wikipedia links in the ancestry. Defaults to ``true``.

Links
-----
For the extension to know where to look for information, simply add a single link to a human-readable Wikipedia page to that entity's links.

Ancestry enrichment
-------------------
The extension will attempt the following for any entity that has a Wikipedia link:

- for places, add coordinates if a place has none already
- for any entity, add additional links to the translations of the given Wikipedia page 
- for any entity that has files, add the primary image of the linked Wikipedia page

Templating
----------

Globals
^^^^^^^

``wikipedia_contributors_copyright_notice`` (:py:class:`betty.wiki.copyright_notice.WikipediaContributors`)
    The copyright notice plugin instance for Wikipedia contributors.

Filters
^^^^^^^

- :py:meth:`wikipedia_summary <betty.project.extension.wiki.Wiki.filter_wikipedia_summary_links>`
