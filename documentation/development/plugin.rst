Plugins
=======

.. toctree::
   :glob:
   :hidden:
   :maxdepth: 1
   :titlesonly:

   plugin/*

Plugins are the mechanism through which optional, drop-in functionality can be provided to Betty.
They are used for a variety of purposes, such as extending the Betty application, or providing additional
ancestry data types.

Plugins must extend :py:class:`betty.plugin.Plugin`:

  .. code-block:: python

      from typing import override
      from betty.locale.localizable import _
      from betty.plugin import Plugin

      class MyPlugin(Plugin):
          @override
          @classmethod
          def plugin_id(cls) -> PluginId:
              return "my-plugin"

          @override
          @classmethod
          def plugin_label(cls) -> Localizable:
              return _("My Plugin")

Plugin types
------------

Plugin types are discovered and made available through :py:class:`betty.plugin.PluginRepository` implementations.
Other than that, there are no guidelines or limitations for what plugins can do, or be used for.

Working with an existing plugin type
------------------------------------
The plugin type's documentation tells you where to find the plugin repository, how to
use the plugins, and how to create your own.

Built-in plugin types
^^^^^^^^^^^^^^^^^^^^^
The following plugin types are provided by Betty itself:

- :doc:`CLI commands </development/plugin/command>`
- :doc:`Copyright notices </development/plugin/copyright-notice>`
- :doc:`Entity types </development/plugin/entity-type>`
- :doc:`Event types </development/plugin/event-type>`
- :doc:`Extensions </development/plugin/extension>`
- :doc:`Genders </development/plugin/gender>`
- :doc:`Licenses </development/plugin/license>`
- :doc:`Place types </development/plugin/place-type>`
- :doc:`Presence roles </development/plugin/presence-role>`
- :doc:`Renderers </development/plugin/renderer>`
- :doc:`Serialization formats </development/plugin/serde-format>`

Creating a new plugin type
--------------------------
If you are developing an API that needs a new plugin type, and you want other developers to be
able to define them as entry points, you **must** create a plugin repository, and you **should** create an abstract
plugin class that extends :py:class:`betty.plugin.Plugin`.

Built-in plugin repository types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:py:class:`betty.plugin.entry_point.EntryPointPluginRepository`
    to discover plugins defined as package entry points.
:py:class:`betty.plugin.lazy.LazyPluginRepositoryBase`
    to easily build repositories that lazily load their plugins.
:py:class:`betty.plugin.proxy.ProxyPluginRepository`
    to discover plugins via one or more upstream plugin repositories.
:py:class:`betty.plugin.static.StaticPluginRepository`
    to discover statically defined plugins.
