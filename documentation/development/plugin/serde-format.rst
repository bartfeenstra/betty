Serialization format plugins
============================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.serde.format.Format`
   * -  Repository
     -  :py:class:`betty.serde.format.FORMAT_REPOSITORY`

Serialization formats allow serializable data, such as project configuration, to be dumped to and loaded from specific
(file) formats such as JSON and YAML.

Creating a serialization format
-------------------------------

Create a new class that extends :py:class:`betty.serde.format.Format` and implements the abstract methods, for example:

.. code-block:: python

   from betty.serde.format import Format, FormatDefinition

   @FormatDefinition(
       id="my-format",
       label=_("My Format"),
   )
   class MyFormat(Format, Plugin):
       # Implement remaining abstract methods...
       ...


Tell Betty about your serialization format by registering it as an entry point. Given the serialization format above in
a module ``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.serde_format']
   'my-module-my-format' = 'my_package.my_module.MyFormat'

