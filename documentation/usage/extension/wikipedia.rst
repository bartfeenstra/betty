The *Wikipedia* extension
=======================
The ``wikipedia`` extension renders summaries of Wikipedia articles. If a entity such as a person or a place contains
links to Wikipedia articles, templates can use this extension to fetch translated summaries of these articles, and
render them on the entity's page.

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
