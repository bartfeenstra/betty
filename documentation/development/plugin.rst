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

The bare minimum requirement for a plugin is to have an ID that is exposed through a plugin definition.

Plugins are discovered through plugin repositories.

Built-in plugin types
---------------------
The following plugin types are provided by Betty itself. Each plugin type's documentation tells you where to find the
plugin repository, how to use the plugins, and how to create your own.

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

Creating a new plugin type
--------------------------

To create a new plugin type, you will need a **plugin type definition**, a **plugin definition class**, and a **plugin
repository**.

Creating a plugin (type) definition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A plugin definition class must subclass :py:class:`betty.plugin.PluginDefinition`. A minimal example is:

   .. code-block:: python

     from typing import ClassVar
     from betty.locale.localizable import _
     from betty.plugin import PluginDefinition, PluginTypeDefinition

     class MyFirstPluginDefinition(PluginDefinition):
        type: ClassVar[PluginTypeDefinition] = PluginTypeDefinition(
            id="my-first-plugin-type",
            Label=_("My First Plugin Type"),
        )

This creates a new plugin type, for which plugins are defined using ``MyFirstPluginDefinition``, and only have an ID.

Your plugin definition class may subclass any of the following base classes, so each plugin can provide additional
metadata in its definition:

:py:class:`betty.plugin.UserFacingPluginDefinition`
    To add human-readable labels and descriptions to plugins.
:py:class:`betty.plugin.CountableUserFacingPluginDefinition`
    To add countable human-readable labels and descriptions to plugins.
:py:class:`betty.plugin.OrderedPluginDefinition`
    To allow plugins to define if they come before or after any other plugins.
:py:class:`betty.plugin.DependentPluginDefinition`
    To allow plugins to define their dependencies on any other plugins.
:py:class:`betty.plugin.ClassedPluginDefinition`
    For plugins that have classes that can be instantiated.

Creating a plugin repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A plugin repository implements :py:class:`betty.plugin.PluginRepository` and is responsible for discovering all plugins
of the type it is responsible for, and making them available to other code. Your plugin repository may subclass one of
the following base classes to get started quickly:

:py:class:`betty.plugin.entry_point.EntryPointPluginRepository`
    to discover plugins defined as package entry points.
:py:class:`betty.plugin.proxy.ProxyPluginRepository`
    to discover plugins via one or more upstream plugin repositories.
:py:class:`betty.plugin.static.StaticPluginRepository`
    to discover statically defined plugins.
