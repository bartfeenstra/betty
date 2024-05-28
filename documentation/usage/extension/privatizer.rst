The *Privatizer* extension
========================
The :py:class:`betty.extension.Privatizer` extension marks entities :doc:`private </usage/ancestry/privacy>`
to prevent sensitive information from being published accidentally.

Entities in Betty have privacy. This is a *ternary* property, with the following possible values:

public (``entity.privacy = betty.model.ancestry.Privacy.PUBLIC``)
    The entity will be included when publishing your ancestry. The privacy **should not** be changed.
private (``entity.privacy = betty.model.ancestry.Privacy.PRIVATE``)
    The entity will not be included when publishing your ancestry. The privacy **should not** be changed.
undetermined (``entity.privacy = betty.model.ancestry.Privacy.UNDETERMINED``)
    The entity is public, but its privacy **may** be determined or changed at will.

The following entities are processed by the Privatizer. They are marked *private* except if any of the following
conditions are met:

People
  People are considered dead past the *lifetime threshold*, which defaults to 125 years, but can be changed in your
  site's :doc:`configuration file <../configuration>`.

  * The person has an end-of-life event, such as a death, final disposition, or will.
  * Any event that was at least the *lifetime threshold* ago.
  * For every person *n* generation(s) before this person, if that person has an end-of-life event at least *n* *
    *lifetime threshold* ago.
  * For every person *n* generation(s) before this person, if that person has any event that was at least (*n* + 1) *
    *lifetime threshold* ago.
  * For every descendant if that person has any event that was at least *lifetime threshold* ago.

  If the Privatizer determines a person private, it will also privatize any events, citations, and files associated
  with that person.

File
  Any citations associated with private files will be privatized.

Event
  Any citations and files associated with private events will be privatized.

Citation
  The source and any files associated with private citations will be privatized.

Source
  Any files associated with private sources will be privatized.

Enable this extension in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          extensions:
            betty.extension.Privatizer: {}

   .. tab-item:: JSON

      .. code-block:: json

          {
            "extensions": {
              "betty.extension.Privatizer": {}
            }
          }

Configuration
-------------
This extension is not configurable.
