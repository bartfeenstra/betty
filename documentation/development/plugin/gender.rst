Gender plugins
==============

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.ancestry.gender.Gender`
   * -  Repository
     -  :py:attr:`betty.project.Project.gender_repository`


Creating a gender
-----------------

#. Create a new class that extends :py:class:`betty.ancestry.gender.Gender` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.ancestry.gender import Gender
     from betty.machine_name import MachineName

     class MyGender(Gender):
       @override
       @classmethod
       def plugin_id(cls) -> MachineName:
           return "my-module-my-gender"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your gender by registering it as an entry point. Given the gender above in a module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.gender']
          'my-module-my-gender' = 'my_package.my_module.MyGender'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.gender': [
                      'my-module-my-gender=my_package.my_module.MyGender',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)

See also
--------
Read more about how to use genders and Betty's built-in genders at :doc:`/usage/ancestry/gender`.
