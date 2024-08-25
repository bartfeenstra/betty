Testing Betty's source code
===========================

In any existing Python environment, run ``./bin/test`` or any of the ``./bin/test-*`` :doc:`commands </development/betty/commands>`.

Environment variables
---------------------

These impact the ``./bin/test`` command:

* ``BETTY_TEST_SKIP_SHELLCHECK=true``: Skip ShellCheck tests.
* ``BETTY_TEST_SKIP_RUFF=true``: Skip Ruff tests.
* ``BETTY_TEST_SKIP_MYPY=true``: Skip mypy tests.
* ``BETTY_TEST_SKIP_STYLELINT=true``: Skip Stylelint tests.
* ``BETTY_TEST_SKIP_ESLINT=true``: Skip ESLint tests.
* ``BETTY_TEST_SKIP_PLAYWRIGHT=true``: Skip Playwright tests.

Fixing problems automatically
-----------------------------
In any existing Python environment, run ``./bin/fix``.
