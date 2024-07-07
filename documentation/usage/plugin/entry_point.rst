Entry point plugins
===================

Plugins may be discovered by defining them as Python distribution package `entry points <https://packaging.python.org/en/latest/specifications/entry-points/>`_.

Creating a plugin type
----------------------
If you are developing an API that needs a new plugin type, and you want other developers to be
able to define them as entry points, you want to use :py:class:`betty.plugin.entry_point.EntryPointPluginRepository`.
It requires an entry point group (name) such as ``YourPluginGroup``, which is also used for the entry point definitions.

Creating a plugin
-----------------
If you are developing a plugin of an existing plugin type that uses entry points, you'll have
to add that plugin to your package metadata. For example, for a plugin type

- whose entry point group is ``YourPluginGroup``
- with a plugin class ``MyPlugin`` in the module ``my_package.my_module``
- and a plugin ID ``my_package_plugin``:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'YourPluginGroup']
          'my_package_plugin' = 'my_package.my_module:MyPlugin'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'YourPluginGroup': [
                      'my_package_plugin=my_package.my_module:MyPlugin',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)