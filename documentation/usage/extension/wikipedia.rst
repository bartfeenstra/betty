The Wikipedia extension
=======================
The :py:class:`betty.extension.Wikipedia` extension renders summaries of Wikipedia articles. If a entity such as a person or a place contains
links to Wikipedia articles, templates can use this extension to fetch translated summaries of these articles, and
render them on the entity's page.

Enable this extension through Betty Desktop, or in your project's :doc:`configuration file </usage/project/configuration>` as follows:

.. code-block:: yaml

    extensions:
      betty.extension.Wikipedia: {}

Configuration
-------------
This extension is not configurable.
