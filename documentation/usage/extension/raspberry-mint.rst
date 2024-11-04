The *Raspberry Mint* extension
==========================
The ``raspberry-mint`` extension provides Betty's default theme.

.. important::
    This extension requires :ref:`Node.js <installation-requirements-nodejs>`.

Enable this extension in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            raspberry-mint: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "raspberry-mint": {}
            }
          }

Configuration
-------------
This extension is configurable:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            raspberry-mint:
              configuration:
                primary_color: '#b3446c'
                secondary_color: '#3eb489'
                tertiary_color: '#ffbd22'
                featured_entities:
                  - entity_type: person
                    entity: P123
                  - entity_type: place
                    entity: Amsterdam

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "raspberry-mint": {
                "configuration" : {
                  "primary_color": "#b3446c",
                  "secondary_color": "#3eb489",
                  "tertiary_color": "#ffbd22",
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

``primary_color``
^^^^^^^^^^^^^^^^^^^^^^^^^^
:sup:`optional`

The case-insensitive hexadecimal code for the primary color. Defaults to ``#b3446c``.

``secondary_color``
^^^^^^^^^^^^^^^^^^^^^^^^^^
:sup:`optional`

The case-insensitive hexadecimal code for the secondary color. Defaults to ``#3eb489``.

``tertiary_color``
^^^^^^^^^^^^^^^^^^^^^^^^^^
:sup:`optional`

The case-insensitive hexadecimal code for the tertiary color. Defaults to ``#ffbd22``.

``featured_entities``
^^^^^^^^^^^^^^^^^^^^^
:sup:`optional`

A list of entities to feature on the front page. Each item has the following configuration:

``featured_entities[].entity_type``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:sup:`required`

The **entity type ID** of the entity (type) to feature, e.g. ``person``.

``featured_entities[].entity``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:sup:`required`

The **entity ID** of the entity to feature, e.g. ``P123``.

Templating
----------

Filters
^^^^^^^

- :py:func:`associated_file_references <betty.project.extension._theme.associated_file_references>`
- :py:func:`person_descendant_families <betty.project.extension._theme.person_descendant_families>`
- :py:func:`person_timeline_events <betty.project.extension._theme.person_timeline_events>`
