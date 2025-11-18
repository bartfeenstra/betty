Gender plugins
==============


Creating a gender
-----------------

Create a new class that extends :py:class:`betty.ancestry.gender.Gender` and implements the abstract methods, for
example:

.. code-block:: python

   from betty.ancestry.gender import Gender, GenderDefinition

   @GenderDefinition(
       id="my-gender",
       label=_("My Gender"),
   )
     class MyGender(Gender):
         pass


Tell Betty about your gender by registering it as an entry point. Given the gender above in a module
``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.gender']
   'my-gender' = 'my_package.my_module.MyGender'

See also
--------
Read more about how to use genders and Betty's built-in genders at :doc:`/usage/ancestry/gender`.
