The *HTTP API Documentation* extension
====================================
The ``http-api-doc`` extension renders interactive and user-friendly HTTP API documentation using
`Swagger UI <https://swagger.io/tools/swagger-ui/>`_.

.. important::
    This extension requires :doc:`npm </usage/npm>`.

Enable this extension in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            http-api-doc: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "http-api-doc": {}
            }
          }

Configuration
-------------
This extension is not configurable.
