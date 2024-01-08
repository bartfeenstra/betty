Development & contributions
===========================

Betty is Free and Open Source Software, designed and maintained by volunteers. As such you are welcome to
`report bugs <https://github.com/bartfeenstra/betty/issues>`_ or
`submit improvements <https://github.com/bartfeenstra/betty/pulls>`_.

First, `fork and clone <https://guides.github.com/activities/forking/>`_ the repository, and navigate to its root directory.

Getting started
---------------
:doc:`Install Betty from source </installation/source>`.

Installation
------------
In any existing Python environment, run ``./bin/build-dev``.

.. _development-translations:

Working on translations
^^^^^^^^^^^^^^^^^^^^^^^

Making changes to the translatable strings in the source code
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Run ``betty update-translations`` to update the translations files with the changes you made.

Adding translations for a language for which no translations exist yet
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Run ``betty init-translation $locale`` where ``$locale`` is an
`IETF BCP 47 language tag <https://tools.ietf.org/html/bcp47>`_.

Testing
-------
In any existing Python environment, run ``./bin/test``.

Environment variables
^^^^^^^^^^^^^^^^^^^^^

These impact the ``./bin/test`` command:

* ``BETTY_TEST_SKIP_SHELLCHECK=true``: Skip ShellCheck tests.
* ``BETTY_TEST_SKIP_FLAKE8=true``: Skip Flake8 tests.
* ``BETTY_TEST_SKIP_MYPY=true``: Skip mypy tests.
* ``BETTY_TEST_SKIP_STYLELINT=true``: Skip Stylelint tests.
* ``BETTY_TEST_SKIP_ESLINT=true``: Skip ESLint tests.
* ``BETTY_TEST_SKIP_CYPRESS=true``: Skip Cypress tests.
* ``BETTY_TEST_SKIP_PYINSTALLER=true``: Skip the PyInstaller test build.

Fixing problems automatically
-----------------------------
In any existing Python environment, run ``./bin/fix``.
