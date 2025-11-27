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
                regional_content:
                  front-page-content:
                    - id: raspberry-mint-featured-entities
                      configuration:
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
                  "regional_content": {
                    "front-page-content":[
                      {
                        "id": "raspberry-mint-featured-entities":
                        "configuration": [
                          {
                            "entity_type": "person",
                            "entity": "P123"
                          },
                          {
                            "entity_type": "place",
                            "entity": "Amsterdam"
                          }
                        ]
                      }
                    ]
                  ]
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

``regional_content``
^^^^^^^^^^^^^^^^^^^^^
:sup:`optional`

Assign content to regions within this theme. Keys are theme regions, and values are sequences of
:doc:`content provider </usage/content-provider>` instance configurations.

``regional_content[][].id``
~~~~~~~~~~~~~~~~~~~~~~~~~~~
:sup:`required`

The plugin ID of the content provider to assign to this region.

``regional_content[][].configuration``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:sup:`optional`

The configuration for the content provider, if needed.

Regions
-------

Raspberry Mint provides the following regions content providers may be configured for:

- ``front-page-content``
  The main content for the front page.
- ``front-page-summary``
  The page summary for the front page.

Templating
----------

Filters
^^^^^^^

- :py:func:`associated_file_references <betty.project.extension._theme.associated_file_references>`
- :py:func:`person_descendant_families <betty.project.extension._theme.person_descendant_families>`
- :py:func:`person_timeline_events <betty.project.extension._theme.person_timeline_events>`
