The anonymizer extension
========================

The *anonymizer* ensures that all resources marked private become anonymous, and that all traces to associated resources
are removed to prevent these associations from accidentally giving away private information. Imagine that your ancestry
contains information about where a person currently lives. If you mark this person as private, the *anonymizer* will
remove the association between this person and the residence event containing their address. Because it is only the
association that is removed, the event itself will remain a part of your ancestry. If you do not want this, you can use
the :doc:`cleaner <cleaner>` extension as well.

The following associations are removed by the *anonymizer* extension:

For people:
    * names and associations between names and their citations
    * citations
    * files
    * presences at events
    * relationships with their parents if they do not have children

For events:
    * citations
    * files
    * people's presences

For files:
    * any resources the file is associated with

For citations:
    * any facts supported by the citation
    * files
    * source

For sources:
    * any parent sources containing the source, or any child sources contained by the source
    * files
    * citations

Configuration
-------------
This extension is not configurable. Enable it in your site's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.anonymizer.Anonymizer: ~
