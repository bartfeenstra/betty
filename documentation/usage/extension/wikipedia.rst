The *Wikipedia* extension
=======================
The :py:class:`betty.extension.Wikipedia` extension renders summaries of Wikipedia articles. If a entity such as a person or a place contains
links to Wikipedia articles, templates can use this extension to fetch translated summaries of these articles, and
render them on the entity's page.

Enable this extension through Betty Desktop, or in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. md-tab-set::

   .. md-tab-item:: YAML

      .. code-block:: yaml

          extensions:
            betty.extension.Wikipedia: {}

   .. md-tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "betty.extension.Wikipedia": {}
            }
          }

Configuration
-------------
This extension is configurable through Betty Desktop or in the configuration file:

.. md-tab-set::

   .. md-tab-item:: YAML

      .. code-block:: yaml

          extensions:
            betty.extension.Wikipedia:
              configuration:
                populate_images: false

   .. md-tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "betty.extension.Wikipedia": {
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
