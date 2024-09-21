Serialization format plugins
============================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.serde.format.Format`
   * -  Repository
     -  :py:class:`betty.serde.format.FORMAT_REPOSITORY`

Serialization formats allow serializable data, such as project configuration, to be dumped to and loaded from specific
(file) formats such as JSON and YAML.

Creating a serialization format
-------------------------------

#. Create a new class that extends :py:class:`betty.serde.format.Format` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.machine_name import MachineName
     from betty.plugin import Plugin
     from betty.serde.format.Format

     class MyFormat(Format, Plugin):
       @override
       @classmethod
       def plugin_id(cls) -> MachineName:
           return "my-module-my-format"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your serialization format by registering it as an entry point. Given the serialization format above
in a module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.serde_format']
          'my-module-my-format' = 'my_package.my_module.MyFormat'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.serde_format': [
                      'my-module-my-format=my_package.my_module.MyFormat',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)
