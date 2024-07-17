Ancestry
========

.. toctree::
   :glob:
   :hidden:
   :maxdepth: 1
   :titlesonly:

   ancestry/*

An ancestry is Betty's main data model. It organizes all the information in your family history
in a way that can easily be used across all parts of Betty. The main components are:

Entities
    An entity is an object that describes a thing, such as a place or a person.
Fields
    Individual pieces of information belonging to an entity, such as a place or person name.
Associations
    A reference between entities, stored in a field on each entity.

A model with lots of data is a graph, a network, like a web of information that can be traversed,
analyzed, expanded, and ultimately generated into a site.

In code, you will be using :py:class:`betty.model.ancestry.Ancestry`, through which you can
access any entity of any type.

.. tab-set::

   .. tab-item:: Python

      .. code-block:: python

          from betty.model.ancestry import Ancestry, Person

          ancestry = Ancestry()
          person = Person(id='a1b2')
          ancestry.add(person)
          assert person is ancestry[Person]['a1b2']

   .. tab-item:: Jinja2

      .. code-block:: jinja

          {% set people = ancestry['person'] %}
          {% set person_a1b2 = people['a1b2'] %}

In this section
---------------
- :doc:`ancestry/citation`
- :doc:`ancestry/date`
- :doc:`ancestry/enclosure`
- :doc:`ancestry/event`
- :doc:`ancestry/event-type`
- :doc:`ancestry/file`
- :doc:`ancestry/file-reference`
- :doc:`ancestry/link`
- :doc:`ancestry/media-type`
- :doc:`ancestry/note`
- :doc:`ancestry/person`
- :doc:`ancestry/person-name`
- :doc:`ancestry/place`
- :doc:`ancestry/place-name`
- :doc:`ancestry/presence`
- :doc:`ancestry/presence-role`
- :doc:`ancestry/privacy`
- :doc:`ancestry/source`

See also
--------
- :doc:`/development/plugin/entity-type`
