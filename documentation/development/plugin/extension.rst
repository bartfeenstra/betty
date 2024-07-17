Extension plugins
=================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.project.extension.Extension`
   * -  Repository
     -  :py:class:`betty.project.extension.EXTENSION_REPOSITORY`

Extensions are core application components, and can be enabled and configured per project. An extension
can do many things, such as loading new or expanding existing ancestry data, or generating additional
content for your site.

Creating an extension
---------------------

#. Create a new class that extends :py:class:`betty.project.extension.Extension` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.project.extension import Extension

     class MyExtension(Extension):
       @override
       @classmethod
       def plugin_id(cls) -> str:
           return "my-module-my-extension"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your extension by registering it as an entry point. Given the extension above in a module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.extension']
          'my-module-my-extension' = 'my_package.my_module.MyExtension'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.extension': [
                      'my-module-my-extension=my_package.my_module.MyExtension',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)

Asset management
----------------
Extensions can enable :doc:`asset management </usage/assets>` to provide translations, templates, and more, by overriding
:py:meth:`betty.project.extension.Extension.assets_directory_path` to return the path on disk where the extension's assets
are located. This may be anywhere in your Python package.

.. code-block:: python

    from typing import override
    from betty.project.extension import Extension

    class MyExtension(Extension):
        @override
        @classmethod
        def assets_directory_path(cls) -> Path | None:
            # A directory named "assets" in the same parent directory as the current Python file.
            return Path(__file__).parent / 'assets'


Dependencies
------------
.. important::
    Any dependencies on other Python packages must be declared by your extension's Python package.

Extensions have fine-grained control over which other extensions they require, and the order in
which they appear in the extension dependency tree:

:py:meth:`betty.project.extension.Extension.depends_on`
    Declare required other extensions. This ensures those extensions are enabled and appear before
    your extension in the extension dependency tree.
:py:meth:`betty.project.extension.Extension.comes_after`
    Declare other extensions that are not required, but if they **are** enabled, then your extension
    will appear after them in the extension dependency tree.
:py:meth:`betty.project.extension.Extension.comes_before`
    Declare other extensions that are not required, but if they **are** enabled, then your extension
    will appear before them in the extension dependency tree.

Optional functionality
----------------------
Extensions can optionally provide the following functionality:

:py:class:`betty.project.extension.ConfigurableExtension`
    Enable configuration management for the extension.
:py:class:`betty.project.extension.Theme`
    Mark the extension as being a theme, e.g. an extension that determines the overall look and
    feel of a site.
:py:class:`betty.html.CssProvider`
    Add additional CSS files to generated pages.
:py:class:`betty.html.JsProvider`
    Add additional JavaScript files to generated pages.
:py:class:`betty.jinja2.Jinja2Provider`
    Integrate the extension with :doc:`Jinja2 </usage/templating>`.

See also
--------
Read more about how to use extensions and Betty's built-in extensions at :doc:`/usage/extension`.
