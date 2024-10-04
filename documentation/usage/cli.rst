The command line
================

The command line is the primary way to interact with Betty:

.. code-block::

    Usage: betty [OPTIONS] COMMAND [ARGS]...

    Options:
      --version  Show the version and exit.
      --help     Show this message and exit.

    Commands:
      clear-caches                   Clear all caches
      config                         Configure Betty
      demo                           Explore a demonstration site
      docs                           View the documentation
      extension-new-translation      Create a new translation for an extension
      extension-update-translations  Update all existing translations for an
                                     extension
      generate                       Generate a static site
      new                            Create a new project
      new-translation                Create a new translation
      serve                          Serve a generated site
      update-translations            Update all existing translations
      dev-new-translation            Create a new translation for Betty itself
      dev-update-translations        Update all existing translations for Betty
                                     itself


Clearing caches
---------------

.. code-block::

    Usage: betty clear-caches [OPTIONS]

      Clear all caches

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


Configuring the Betty application
---------------------------------

.. code-block::

    Usage: betty config [OPTIONS]

      Configure Betty

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --locale TEXT         Set the locale for Betty's user interface. This must be
                            an IETF BCP 47 language tag.
      --help                Show this message and exit.


Explore a Betty demonstration site
----------------------------------

.. code-block::

    Usage: betty demo [OPTIONS]

      Explore a demonstration site

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


View the Betty documentation
----------------------------

.. code-block::

    Usage: betty docs [OPTIONS]

      View the documentation

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


Generate a site for your project
--------------------------------

.. code-block::

    Usage: betty generate [OPTIONS]

      Generate a static site

    Options:
      -v, --verbose             Show verbose output, including informative log
                                messages.
      -vv, --more-verbose       Show more verbose output, including debug log
                                messages.
      -vvv, --most-verbose      Show most verbose output, including all log
                                messages.
      -c, --configuration TEXT  The path to a Betty project configuration file.
                                Defaults to betty.json|yaml|yml in the current
                                working directory.
      --help                    Show this message and exit.


Create a new project
--------------------

.. code-block::

    Usage: betty new [OPTIONS]

      Create a new project

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


Create a new translation for your project
-----------------------------------------

.. code-block::

    Usage: betty new-translation [OPTIONS] LOCALE

      Create a new translation

    Options:
      -v, --verbose             Show verbose output, including informative log
                                messages.
      -vv, --more-verbose       Show more verbose output, including debug log
                                messages.
      -vvv, --most-verbose      Show most verbose output, including all log
                                messages.
      -c, --configuration TEXT  The path to a Betty project configuration file.
                                Defaults to betty.json|yaml|yml in the current
                                working directory.
      --help                    Show this message and exit.


Update all translations for your project
----------------------------------------

.. code-block::

    Usage: betty update-translations [OPTIONS]

      Update all existing translations

    Options:
      -v, --verbose             Show verbose output, including informative log
                                messages.
      -vv, --more-verbose       Show more verbose output, including debug log
                                messages.
      -vvv, --most-verbose      Show most verbose output, including all log
                                messages.
      --source TEXT
      --exclude TEXT
      -c, --configuration TEXT  The path to a Betty project configuration file.
                                Defaults to betty.json|yaml|yml in the current
                                working directory.
      --help                    Show this message and exit.


Create a new translation for your extension
-------------------------------------------

.. code-block::

    Usage: betty extension-new-translation [OPTIONS] EXTENSION LOCALE

      Create a new translation for an extension

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --help                Show this message and exit.


Update all translations for your extension
------------------------------------------

.. code-block::

    Usage: betty extension-update-translations [OPTIONS] EXTENSION SOURCE

      Update all existing translations for an extension

    Options:
      -v, --verbose         Show verbose output, including informative log messages.
      -vv, --more-verbose   Show more verbose output, including debug log messages.
      -vvv, --most-verbose  Show most verbose output, including all log messages.
      --exclude TEXT
      --help                Show this message and exit.


Serve your project's generated site
-----------------------------------

.. code-block::

    Usage: betty serve [OPTIONS]

      Serve a generated site

    Options:
      -v, --verbose             Show verbose output, including informative log
                                messages.
      -vv, --more-verbose       Show more verbose output, including debug log
                                messages.
      -vvv, --most-verbose      Show most verbose output, including all log
                                messages.
      -c, --configuration TEXT  The path to a Betty project configuration file.
                                Defaults to betty.json|yaml|yml in the current
                                working directory.
      --help                    Show this message and exit.
