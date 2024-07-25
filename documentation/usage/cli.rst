The command line
================

The command line is the primary way to interact with Betty:

.. code-block::

    Usage: betty [OPTIONS] COMMAND [ARGS]...

    Options:
      --version  Show the version and exit.
      --help     Show this message and exit.

    Commands:
      clear-caches             Clear all caches.
      config                   Configure Betty.
      demo                     Explore a demonstration site.
      docs                     View the documentation.
      generate                 Generate a static site.
      new                      Create a new project.
      serve                    Serve a generated site.
      serve-nginx-docker       Serve a generated site with nginx in a Docker...
      dev-init-translation     Initialize a new translation
      dev-update-translations  Update all existing translations


Clearing caches
---------------

.. code-block::

    Usage: betty clear-caches [OPTIONS]

      Clear all caches.

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


Configuring the Betty application
---------------------------------

.. code-block::

    Usage: betty config [OPTIONS]

      Configure Betty.

    Options:
      --locale TEXT         Set the locale for Betty's user interface. This must be
                            an IETF BCP 47 language tag.
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


Explore a Betty demonstration site
----------------------------------

.. code-block::

    Usage: betty demo [OPTIONS]

      Explore a demonstration site.

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


View the Betty documentation
----------------------------

.. code-block::

    Usage: betty docs [OPTIONS]

      View the documentation.

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


Generate a site for your project
--------------------------------

.. code-block::

    Usage: betty generate [OPTIONS]

      Generate a static site.

    Options:
      -c, --configuration TEXT  The path to a Betty project configuration file.
                                Defaults to betty.json|yaml|yml in the current
                                working directory.
      -v, --verbose             Show verbose output, including informative log
                                messages.
      -vv, --more-verbose       Show more verbose output, including debug log
                                messages.
      -vvv, --most-verbose      Show most verbose output, including all log
                                messages.
      --help                    Show this message and exit.


Create a new project
--------------------

.. code-block::

    Usage: betty new [OPTIONS]

      Create a new project.

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


Serve your project's generated site
-----------------------------------

.. code-block::

    Usage: betty serve [OPTIONS]

      Serve a generated site.

    Options:
      -c, --configuration TEXT  The path to a Betty project configuration file.
                                Defaults to betty.json|yaml|yml in the current
                                working directory.
      -v, --verbose             Show verbose output, including informative log
                                messages.
      -vv, --more-verbose       Show more verbose output, including debug log
                                messages.
      -vvv, --most-verbose      Show most verbose output, including all log
                                messages.
      --help                    Show this message and exit.


Serve your project's generated site using nginx and Docker
----------------------------------------------------------

.. code-block::

    Usage: betty serve-nginx-docker [OPTIONS]

      Serve a generated site with nginx in a Docker container.

    Options:
      -c, --configuration TEXT  The path to a Betty project configuration file.
                                Defaults to betty.json|yaml|yml in the current
                                working directory.
      -v, --verbose             Show verbose output, including informative log
                                messages.
      -vv, --more-verbose       Show more verbose output, including debug log
                                messages.
      -vvv, --most-verbose      Show most verbose output, including all log
                                messages.
      --help                    Show this message and exit.
