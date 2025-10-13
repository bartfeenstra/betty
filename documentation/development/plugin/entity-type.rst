Entity type plugins
===================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.model.Entity`
   * -  Repository
     -  :py:attr:`betty.project.Project.entity_type_repository`

Entity types form the core of a Betty project's ancestry. Each entity type describes a specific type of information,
such as people or places. Ancestries can be filled with an unlimited number of entities (instances of entity types),
that together describe a family's history.

Creating an entity type
-----------------------

Create a new class that extends :py:class:`betty.model.Entity` and implements the abstract methods, for example:

.. code-block:: python

   from betty.model import Entity, EntityDefinition

   @EntityDefinition(
       id="my-entity",
       label=_("My Entity"),
   )
   class MyEntity(Entity):
       # Implement remaining abstract methods...
       ...


Tell Betty about your entity type by registering it as an entry point. Given the entity type above in a module
``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.entity_type']
   'my-entity' = 'my_package.my_module.MyEntity.plugin'

See also
--------
Read more about how to use entities and Betty's built-in entity types at :doc:`/usage/ancestry`.
