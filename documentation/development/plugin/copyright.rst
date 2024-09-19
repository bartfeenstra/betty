Copyright plugins
==============

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.copyright.Copyright`
   * -  Repository
     -  :py:class:`betty.project.Project.copyrights`
            All copyrights, including those defined in the project configuration
        :py:class:`betty.copyright.COPYRIGHT_REPOSITORY`
            Only copyrights available to any project


Creating a copyright
--------------------

#. Create a new class that extends :py:class:`betty.copyright.Copyright` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.copyright import Copyright
     from betty.machine_name import MachineName

     class MyCopyright(Copyright):
       @override
       @classmethod
       def plugin_id(cls) -> MachineName:
           return "my-module-my-copyright"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your copyright by registering it as an entry point. Given the copyright above in a module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.copyright']
          'my-module-my-copyright' = 'my_package.my_module.MyCopyright'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.copyright': [
                      'my-module-my-copyright=my_package.my_module.MyCopyright',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)

See also
--------
Read more about how to use copyrights and Betty's built-in copyrights at :doc:`/usage/copyright`.
