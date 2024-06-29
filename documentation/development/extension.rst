Developing a Betty extension
============================

Extensions are Betty plugins that integrate deeply with the Betty application and have the most power
to change or add functionality to your sites.

Getting started
---------------

#. Determine where in your package you want the extension to be located. Its fully qualified name will be
   used as its extension name, e.g. an extension ``my_package.my_module.MyExtension`` will be named
   ``"my_package.my_module.MyExtension"``. This name is also used to enable the extension in
   :doc:`project configuration files </usage/project/configuration>`.

#. Create a new class that extends :py:class:`betty.project.extension.Extension`, for example:
  .. code-block:: python

      from betty.project.extension import Extension

      class MyExtension(Extension):
        pass

Congratulations! You have created your very first Betty extension. Keep reading to learn how to add
functionality.

Making your extension discoverable
----------------------------------
Making your extension discoverable means that Betty knows it's available and can present users with the option
to enable and configure your extension for their project.

Given an extension ``my_package.my_module.MyExtension``, add the following to your extension's Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.extensions']
          'my_package.my_module.MyExtension' = 'my_package.my_module.MyExtension'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.extensions': [
                      'my_package.my_module.MyExtension=my_package.my_module.MyExtension',
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

    from betty.project.extension import Extension

    class MyExtension(Extension):
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

Dispatching
-----------
Extensions can handle dispatched events by extending from any of the following classes:

:py:class:`betty.project.extension.ConfigurableExtension`
    Enable configuration management for the extension.
:py:class:`betty.project.extension.Theme`
    Mark the extension as being a theme, e.g. an extension that determines the overall look and
    feel of a site.
:py:class:`betty.project.extension.UserFacingExtension`
    Mark the extension as being suitable for end user interaction, e.g. it is not internal.
:py:class:`betty.generate.Generator`
    Dispatched when the site is being generated. This is used to tell extensions when to
    generate their parts of the site.
:py:class:`betty.gui.GuiBuilder`
    Provide a Graphical User Interface to manage the extension in the Betty Desktop application.
:py:class:`betty.html.CssProvider`
    Add additional CSS files to generated pages.
:py:class:`betty.html.JsProvider`
    Add additional JavaScript files to generated pages.
:py:class:`betty.jinja2.Jinja2Provider`
    Integrate the extension with :doc:`Jinja2 </usage/templating>`.
:py:class:`betty.load.Loader`
    Dispatched when data is loaded into an ancestry. This is used to import data.
:py:class:`betty.load.PostLoader`
    Dispatched after data is loaded into an ancestry. This is used to modify loaded data.
