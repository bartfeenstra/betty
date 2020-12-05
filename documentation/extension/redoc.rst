The ReDoc extension
===================

The *ReDoc* extension renders interactive and user-friendly HTTP API documentation using
`ReDoc <https://github.com/Redocly/redoc>`_.

Requirements
------------

* `Node.js 10+ <https://nodejs.org/>`_
* npm must be available using the ``npm`` command.

Configuration
-------------
This extension is not configurable. Enable it in your site's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.redoc.ReDoc: ~
