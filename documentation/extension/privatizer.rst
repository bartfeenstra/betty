The privatizer extension
========================

The *privatizer* marks resources private to prevent sensitive information from being published accidentally. It is most
powerful in achieving this when used in combination with the :doc:`anonymizer <anonymizer>` and :doc:`cleaner <cleaner>`
extensions.

Resources in Betty have privacy. This is a *ternary* property, with the following possible values:

public (``resource.private = False``)
    The resource will be included when publishing your ancestry. The privacy **should not** be changed.
private (``resource.private = True``)
    The resource will not be included when publishing your ancestry. The privacy **should not** be changed.
undecided (``resource.private = None``)
    The resource is public, but its privacy **may** be determined or changed at will.

The following resources are processed by the *privatizer*. They are marked *private* except if any of the following
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

  If the *privatizer* determines a person private, it will also privatize any events, citations, and files associated
  with that person.

File
  Any citations associated with private files will be privatized.

Event
  Any citations and files associated with private events will be privatized.

Citation
  The source and any files associated with private citations will be privatized.

Source
  Any files associated with private sources will be privatized.

Configuration
-------------
This extension is not configurable. Enable it in your site's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.privatizer.Privatizer: ~
