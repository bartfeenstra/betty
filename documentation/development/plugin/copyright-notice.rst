Copyright notice plugins
========================


Creating a copyright
--------------------

Create a new class that extends :py:class:`betty.copyright_notice.CopyrightNotice` and implements the abstract methods,
for example:

.. code-block:: python

   from betty.copyright import CopyrightNotice, CopyrightNoticeDefinition

   @CopyrightNoticeDefinition(
       id="my-copyright-notice",
       label=_("My Copyright Notice"),
   )
   class MyCopyrightNotice(CopyrightNotice):
       # Implement remaining abstract methods...
       ...


Tell Betty about your copyright notice by registering it as an entry point. Given the copyright notice above in a module ``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.copyright_notice']
   'my-copyright-notice' = 'my_package.my_module.MyCopyrightNotice'

See also
--------
Read more about how to use copyright notices and Betty's built-in copyright notices at :doc:`/usage/copyright-notice`.
