Development & contributions
===========================

Betty is Free and Open Source Software, designed and maintained by volunteers. As such you are welcome to
`report bugs <https://github.com/bartfeenstra/betty/issues>`_ or
`submit improvements <https://github.com/bartfeenstra/betty/pulls>`_.

First, `fork and clone <https://guides.github.com/activities/forking/>`_ the repository, and navigate to its root directory.

Requirements
------------
- The :doc:`installation requirements <installation>` to run Betty
- `Node.js 10+ <https://nodejs.org/>`_ (optional)
- `Docker <https://www.docker.com/>`_ if you are on Linux
- Bash (you're all good if ``which bash`` outputs a path in your terminal)

Installation
------------
In any existing Python environment, run ``./bin/build-dev``.

.. _development-translations:

Adding or updating translations
-------------------------------
To add a new translation, run ``./bin/init-translation $locale`` where ``$locale`` is an
`IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag, but using underscores instead of dashes (``nl_NL``
instead of ``nl-NL``).

After making changes to the translatable strings in the source code, run ``./bin/extract-translatables``.

Testing
-------
In any existing Python environment, run ``./bin/test``.

Fixing problems automatically
-----------------------------
In any existing Python environment, run ``./bin/fix``.
