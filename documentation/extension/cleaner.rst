The cleaner extension
=====================

The *cleaner* removes all anonymous resources (resources not associated with any other resources) from your ancestry.
Imagine that your ancestry contains a place that is not associated with any event, or a file not associated with any
resource. The *cleaner* will remove them automatically.

The following resources are removed by the *cleaner* extension:

People
    * if they are private, and
    * if they have no children

Events
    * if no people were present

Places
    * if no events took place here, and
    * if the place does not contain any other places

Files
    * if no resources are associated with the file, and
    * if the file has no citations

Citations
    * if no facts reference the citation, and
    * if the citation has no files

Sources
    * if no citations reference the source, and
    * if the source is not contained by another source, and
    * if the source does not contain any other sources, and
    * if the source has no files

Configuration
-------------
This extension is not configurable. Enable it in your site's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.cleaner.Cleaner: ~
