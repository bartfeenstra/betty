
The command line
================

After installation, Betty can be used via the `betty` command:

.. code-block::

    Usage: betty [OPTIONS] COMMAND [ARGS]...

    Options:
      -c, --configuration TEXT  The path to a Betty configuration file. Defaults
                                to betty.json|yaml|yml in the current working
                                directory. This will make additional commands
                                available.

      --version                 Show the version and exit.
      --help                    Show this message and exit.

    Commands:
      document      View the documentation.
      clear-caches  Clear all caches.
      generate      Generate a static site.
      serve         Serve a generated site.

Generally you will be using Betty for a specific site. When you call ``betty`` with a
:doc:`configuration file <configuration>` (e.g. ``betty -c betty.yaml``), additional commands provided by the extensions
enabled in the configuration file may become available.
