Place type plugins
==================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.ancestry.place_type.PlaceType`
   * -  Repository
     -  :py:attr:`betty.project.Project.place_type_repository`

Place types are used to indicate the **type** of a :doc:`/usage/ancestry/place`, such as a country, a city, or a house
number.

Creating a place type
---------------------

#. Create a new class that extends :py:class:`betty.ancestry.place_type.PlaceType` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.ancestry.place_type import PlaceType
     from betty.machine_name import MachineName

     class MyPlaceType(PlaceType):
       @override
       @classmethod
       def plugin_id(cls) -> MachineName:
           return "my-module-my-place-type"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your place type by registering it as an entry point. Given the place type above in a module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.place_type']
          'my-module-my-place-type' = 'my_package.my_module.MyPlaceType'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.place_type': [
                      'my-module-my-place-type=my_package.my_module.MyPlaceType',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)

See also
--------
Read more about how to use place types and Betty's built-in place types at :doc:`/usage/ancestry/place-type`.
