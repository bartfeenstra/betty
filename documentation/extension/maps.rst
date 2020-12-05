The maps extension
==================

The *maps* extension renders interactive maps using `Leaflet <https://leafletjs.com/>`_ and
`OpenStreetMap <https://www.openstreetmap.org/>`_.

Requirements
------------

* `Node.js 10+ <https://nodejs.org/>`_
* npm must be available using the ``npm`` command.

Configuration
-------------
This extension is not configurable. Enable it in your site's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.maps.Maps: ~
