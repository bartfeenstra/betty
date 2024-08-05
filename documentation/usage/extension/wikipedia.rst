The *Wikipedia* extension
=======================
The ``wikipedia`` extension enriches your ancestry and site with content from Wikipedia.

Enable this extension in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            wikipedia: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "wikipedia": {}
            }
          }

Configuration
-------------
This extension is configurable:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            wikipedia:
              configuration:
                populate_images: false

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "wikipedia": {
                "configuration" : {
                  "populate_images": false
                }
              }
            }
          }


All configuration options
^^^^^^^^^^^^^^^^^^^^^^^^^
- ``populate_images`` (optional): A boolean indicating whether to download images from the Wikipedia
  links in the ancestry. Defaults to ``true``.

Links
-----
For the extension to know where to look for it's information, simply add a single link to a human-readable Wikipedia page to that entity's links.

Ancestry enrichment
-------------------
The extension will attempt the following for any entity that has a Wikipedia link:

- for places, add coordinates if a place has none already
- for any entity, add additional links to the translations of the given Wikipedia page 
- for any entity that has files, add the primary image of the linked Wikipedia page
