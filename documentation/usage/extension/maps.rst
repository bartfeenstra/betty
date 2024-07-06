The *Maps* extension
==================
The :py:class:`betty.extension.Maps` extension renders interactive maps using `Leaflet <https://leafletjs.com/>`_ and
`OpenStreetMap <https://www.openstreetmap.org/>`_.

.. important::
    This extension requires :doc:`npm </usage/npm>`.

Enable this extension in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            betty.extension.Maps: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "betty.extension.Maps": {}
            }
          }

Configuration
-------------
This extension is not configurable.
