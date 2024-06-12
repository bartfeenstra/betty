The *Cotton Candy* extension
==========================
The :py:class:`betty.extension.CottonCandy` extension provides Betty's default theme.

.. important::
    This extension requires :doc:`npm </usage/npm>`.

Enable this extension through Betty Desktop, or in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            betty.extension.CottonCandy: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "betty.extension.CottonCandy": {}
            }
          }

Configuration
-------------
This extension is configurable through Betty Desktop or in the configuration file:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

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
                logo: my-ancestry-logo.png

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "betty.extension.CottonCandy": {
                "configuration" : {
                  "primary_inactive_color": "#ffc0cb",
                  "primary_active_color": "#ff69b4",
                  "link_inactive_color": "#149988",
                  "link_active_color": "#2a615a",
                  "featured_entities": [
                    {
                      "entity_type": "Person",
                      "entity_id": "P123"
                    },
                    {
                      "entity_type": "Place",
                      "entity_id": "Amsterdam"
                    }
                  ],
                  "logo": "my-ancestry-logo.png"
                }
              }
            }
          }

All configuration options
^^^^^^^^^^^^^^^^^^^^^^^^^
- ``primary_inactive_color`` (optional): The case-insensitive hexadecimal code for the primary color. Defaults to
  ``#ffc0cb``.
- ``primary_active_color`` (optional): The case-insensitive hexadecimal code for the primary color for actively
  engaged elements. Defaults to ``#ff69b4``.
- ``link_inactive_color`` (optional): The case-insensitive hexadecimal code for the link color. Defaults to ``#149988``.
- ``link_active_color`` (optional): The case-insensitive hexadecimal code for the color of actively engaged links.
  Defaults to ``#2a615a``.
- ``featured_entities`` (optional): A list of entities to feature on the front page. Each item has the following
  configuration:

  - ``entity_type`` (required): The name of the entity type to feature, e.g. ``Person``.
  - ``entity_id`` (required):  The ID of the entity type to feature, e.g. ``P123``.
- ``logo`` (optional): The path to your site's logo file. Defaults to the Betty logo.