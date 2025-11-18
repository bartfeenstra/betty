Place type plugins
==================

Place types are used to indicate the **type** of a :doc:`/usage/ancestry/place`, such as a country, a city, or a house
number.

Creating a place type
---------------------

Create a new class that extends :py:class:`betty.ancestry.place_type.PlaceType` and implements the abstract methods, for
example:

.. code-block:: python

   from betty.ancestry.place_type import PlaceType, PlaceTypeDefinition

   @PlaceTypeDefinition(
       id="my-place-type",
       label=_("My Place Type"),
   )
   class MyPlaceType(PlaceType):
       pass


Tell Betty about your place type by registering it as an entry point. Given the place type above in a module ``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.place_type']
   'my-module-my-place-type' = 'my_package.my_module.MyPlaceType'

See also
--------
Read more about how to use place types and Betty's built-in place types at :doc:`/usage/ancestry/place-type`.
