The *Maps* extension
==================
The :py:class:`betty.extension.Maps` extension renders interactive maps using `Leaflet <https://leafletjs.com/>`_ and
`OpenStreetMap <https://www.openstreetmap.org/>`_.

Enable this extension through Betty Desktop, or in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. md-tab-set::

   .. md-tab-item:: YAML

      .. code-block:: yaml

          extensions:
            betty.extension.Maps: {}

   .. md-tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "betty.extension.Maps": {}
            }
          }

Configuration
-------------
This extension is not configurable.
