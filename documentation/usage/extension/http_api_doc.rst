The *HTTP API Documentation* extension
====================================
The :py:class:`betty.extension.HttpApiDoc` extension renders interactive and user-friendly HTTP API documentation using
`ReDoc <https://github.com/Redocly/redoc>`_.

.. important::
    This extension requires :doc:`npm </usage/npm>`.

Enable this extension through Betty Desktop, or in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. md-tab-set::

   .. md-tab-item:: YAML

      .. code-block:: yaml

          extensions:
            betty.extension.HttpApiDoc: {}

   .. md-tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "betty.extension.HttpApiDoc": {}
            }
          }

Configuration
-------------
This extension is not configurable.
