The command line
================

The command line is the primary way to interact with Betty:

.. code-block::

    Usage: betty [OPTIONS] COMMAND [ARGS]...

    Options:
      -c, --configuration TEXT  The path to a Betty project configuration file.
                                Defaults to betty.json|yaml|yml in the current
                                working directory. This will make additional
                                commands available.
      -v, --verbose             Show verbose output, including informative log
                                messages.
      -vv, --more-verbose       Show more verbose output, including debug log
                                messages.
      -vvv, --most-verbose      Show most verbose output, including all log
                                messages.
      --version                 Show the version and exit.
      --help                    Show this message and exit.

    Commands:
      docs                 View the documentation.
      clear-caches         Clear all caches.
      demo                 Explore a demonstration site.
      init-translation     Initialize a new translation
      update-translations  Update all existing translations
      generate             Generate a static site.
      serve                Serve a generated site.
      serve-nginx-docker   Serve a generated site with nginx in a Docker...
