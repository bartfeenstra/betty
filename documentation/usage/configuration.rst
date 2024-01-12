Application configuration
=========================

Betty uses global application configuration for settings that do not impact your projects, such
as the language you want to use Betty in, e.g. for the desktop application and logs. This configuration
can be managed through the desktop application as well as through a configuration file.

The application configuration file is written in JSON and placed at ``$HOME/.betty/configuration/app.json``.
An example configuration:

.. code-block:: json

    {
      "locale": "nl-NL"
    }

All configuration options
-------------------------

- ``locale`` (optional): An `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
  If no locale is specified, Betty defaults to US English (``en-US``).
