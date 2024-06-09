Plugins
=======

.. toctree::
   :glob:
   :hidden:
   :maxdepth: 1
   :titlesonly:

   plugin/*

*Plugins* are the mechanism through which optional functionality can be provided to Betty.

Each plugin must extend and implement :py:class:`betty.plugin.Plugin`, which provides the ability
for the plugin to identify itself.

In this section
---------------
- :doc:`plugin/entry_point`
