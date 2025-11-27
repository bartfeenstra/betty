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

- :doc:`Console commands </development/plugin/command>`
- :doc:`Content providers </development/plugin/content-provider>`
- :doc:`Copyright notices </development/plugin/copyright-notice>`
- :doc:`Entity types </development/plugin/entity-type>`
- :doc:`Event types </development/plugin/event-type>`
- :doc:`Extensions </development/plugin/extension>`
- :doc:`Genders </development/plugin/gender>`
- :doc:`HTTP rate limits </development/plugin/http-rate-limit>`
- :doc:`Licenses </development/plugin/license>`
- :doc:`Place types </development/plugin/place-type>`
- :doc:`Presence roles </development/plugin/presence-role>`
- :doc:`Renderers </development/plugin/renderer>`
- :doc:`Serialization formats </development/plugin/format>`

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
            "my-first-plugin-type",
            _("My First Plugin Type"),
        )

This creates a new plugin type, for which plugins are defined using ``MyFirstPluginDefinition``, and only have an ID.

Your plugin definition class may subclass any of the following base classes, so each plugin can provide additional
metadata in its definition:

:py:class:`betty.plugin.human_facing.HumanFacingPluginDefinition`
    To add human-readable labels and descriptions to plugins.
:py:class:`betty.plugin.human_facing.CountableHumanFacingPluginDefinition`
    To add countable human-readable labels and descriptions to plugins.
:py:class:`betty.plugin.ordered.OrderedPluginDefinition`
    To allow plugins to define if they come before or after any other plugins.
:py:class:`betty.plugin.dependent.DependentPluginDefinition`
    To allow plugins to define their dependencies on any other plugins.
