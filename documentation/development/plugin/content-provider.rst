Content provider plugins
========================


Creating a content provider
---------------------------

Create a new class that extends :py:class:`betty.content_provider.ContentProvider` and implements the abstract methods,
for example:

.. code-block:: python

   from betty.content_provider import ContentProvider, ContentProviderDefinition

   @ContentProviderDefinition("my-content-provider", _("My Content Provider"))
   class MyContentProvider(ContentProvider):
       # Implement remaining abstract methods...
       ...


Tell Betty about your content provider by registering it as an entry point. Given the content provider above in a module
``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.content_provider']
   'my-content-provider' = 'my_package.my_module.MyContentProvider'
