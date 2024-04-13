Testing Betty's source code
===========================

In any existing Python environment, run ``./bin/test``.

Environment variables
---------------------

These impact the ``./bin/test`` command:

* ``BETTY_TEST_SKIP_SHELLCHECK=true``: Skip ShellCheck tests.
* ``BETTY_TEST_SKIP_FLAKE8=true``: Skip Flake8 tests.
* ``BETTY_TEST_SKIP_MYPY=true``: Skip mypy tests.
* ``BETTY_TEST_SKIP_STYLELINT=true``: Skip Stylelint tests.
* ``BETTY_TEST_SKIP_ESLINT=true``: Skip ESLint tests.
* ``BETTY_TEST_SKIP_BUSTED=true``: Skip the Busted test build.
* ``BETTY_TEST_SKIP_PLAYWRIGHT=true``: Skip Playwright tests.
* ``BETTY_TEST_SKIP_PYINSTALLER=true``: Skip the PyInstaller test build.

Fixing problems automatically
-----------------------------
In any existing Python environment, run ``./bin/fix``.
