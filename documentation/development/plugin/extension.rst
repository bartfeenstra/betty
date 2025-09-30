Extension plugins
=================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.project.extension.Extension`
   * -  Repository
     -  :py:class:`betty.project.Project.extension_repository`

Extensions are core application components, and can be enabled and configured per project. An extension
can do many things, such as loading new or expanding existing ancestry data, or generating additional
content for your site.

Creating an extension
---------------------

Create a new class that extends :py:class:`betty.project.extension.Extension` and implements the abstract methods, for
example:

.. code-block:: python

   from betty.project.extension import Extension, ExtensionDefinition

   @ExtensionDefinition(
       id="my-extension",
       label=_("My Extension"),
   )
   class MyExtension(Extension):
       pass

Tell Betty about your extension by registering it as an entry point. Given the extension above in a module
``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.extension']
   'my-extension' = 'my_package.my_module.MyExtension.plugin'

Optional functionality
----------------------
Extensions can optionally provide the following functionality:

:py:class:`betty.project.extension.ConfigurableExtension`
    Enable configuration management for the extension.
:py:class:`betty.html.CssProvider`
    Add additional CSS files to generated pages.
:py:class:`betty.html.JsProvider`
    Add additional JavaScript files to generated pages.
:py:class:`betty.html.NavigationLinkProvider`
    Add additional navigation links to generated pages.
:py:class:`betty.jinja2.Jinja2Provider`
    Integrate the extension with :doc:`Jinja2 </usage/templating>`.

See also
--------
Read more about how to use extensions and Betty's built-in extensions at :doc:`/usage/extension`.
