License plugins
===============

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.license.License`
   * -  Repository
     -  :py:attr:`betty.project.Project.license_repository`


Creating a license
------------------

#. Create a new class that extends :py:class:`betty.license.License` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.license import License
     from betty.machine_name import MachineName

     class MyLicense(License):
       @override
       @classmethod
       def plugin_id(cls) -> MachineName:
           return "my-module-my-license"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your license by registering it as an entry point. Given the license above in a
module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.license']
          'my-module-my-license' = 'my_package.my_module.MyLicense'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.license': [
                      'my-module-my-license=my_package.my_module.MyLicense',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)

See also
--------
Read more about how to use licenses and Betty's built-in licenses at :doc:`/usage/license`.
