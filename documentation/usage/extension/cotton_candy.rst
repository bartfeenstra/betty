The *Cotton Candy* extension
==========================
The ``cotton-candy`` extension provides Betty's default theme.

.. important::
    This extension requires :doc:`npm </usage/npm>`.

Enable this extension in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            cotton-candy: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "cotton-candy": {}
            }
          }

Configuration
-------------
This extension is configurable:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            cotton-candy:
              configuration:
                primary_inactive_color: '#ffc0cb'
                primary_active_color: '#ff69b4'
                link_inactive_color: '#149988'
                link_active_color: '#2a615a'
                featured_entities:
                  - entity_type: person
                    entity: P123
                  - entity_type: place
                    entity: Amsterdam

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "cotton-candy": {
                "configuration" : {
                  "primary_inactive_color": "#ffc0cb",
                  "primary_active_color": "#ff69b4",
                  "link_inactive_color": "#149988",
                  "link_active_color": "#2a615a",
                  "featured_entities": [
                    {
                      "entity_type": "person",
                      "entity": "P123"
                    },
                    {
                      "entity_type": "place",
                      "entity": "Amsterdam"
                    }
                  ],
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

  - ``entity_type`` (required): The **entity type ID** of the entity (type) to feature, e.g. ``person``.
  - ``entity`` (required):  The **entity ID** of the entity to feature, e.g. ``P123``.