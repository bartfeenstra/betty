The Gramps extension
====================

The *Gramps* extension loads resources from Gramps family trees into your Betty ancestry.

Configuration
-------------
This extension is configurable. Enable it in your site's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.deriver.Deriver:
        family_trees:
          - file: ./gramps.gpkg

* ``family_trees`` (required): An array defining zero or more Gramps family trees to load. Each item is an object with
  the following keys:

      * ``file`` (required): the path to a *Gramps XML* or *Gramps XML Package* file.

  If multiple family trees contain resources of the same type and with the same ID (e.g. a person with ID ``I1234``) each
  resource will overwrite any previously loaded resource.
