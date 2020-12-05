The Wikipedia extension
=======================

The *Wikipedia* extension renders summaries of Wikipedia articles. If a resource such as a person or a place contains
links to Wikipedia articles, templates can use this extension to fetch translated summaries of these articles, and
render them on the resource's page.

Configuration
-------------
This extension is not configurable. Enable it in your site's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.wikipedia.Wikipedia: ~
