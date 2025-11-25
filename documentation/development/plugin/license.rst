License plugins
===============


Creating a license
------------------

Create a new class that extends :py:class:`betty.license.License` and implements the abstract methods, for example:

.. code-block:: python

   from betty.license import License, LicenseDefinition

   @LicenseDefinition("my-license", _("My License"))
   class MyLicense(License):
       # Implement remaining abstract methods...
       ...


Tell Betty about your license by registering it as an entry point. Given the license above in a module
``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.license']
   'my-module-my-license' = 'my_package.my_module.MyLicense'

See also
--------
Read more about how to use licenses and Betty's built-in licenses at :doc:`/usage/license`.
