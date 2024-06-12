The *Trees* extension
===================
The :py:class:`betty.extension.Trees` extension renders interactive family trees using `Cytoscape.js <http://js.cytoscape.org/>`_.

.. important::
    This extension requires :doc:`npm </usage/npm>`.

Enable this extension through Betty Desktop, or in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            betty.extension.Trees: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "betty.extension.Trees": {}
            }
          }

Configuration
-------------
This extension is not configurable.
