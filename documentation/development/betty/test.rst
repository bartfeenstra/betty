Testing Betty's source code
===========================

In any existing Python environment, run ``./bin/test.py`` or any of the ``./bin/test-*.py``
:doc:`commands </development/betty/commands>`.

Environment variables
---------------------

These impact the ``./bin/test.py`` command:

* ``BETTY_TEST_SKIP_RUFF=true``: Skip Ruff tests.
* ``BETTY_TEST_SKIP_STYLELINT=true``: Skip Stylelint tests.
* ``BETTY_TEST_SKIP_TSC=true``: Skip tsc tests.
* ``BETTY_TEST_SKIP_ESLINT=true``: Skip ESLint tests.
* ``BETTY_TEST_SKIP_PLAYWRIGHT=true``: Skip Playwright tests.
* ``BETTY_TEST_SKIP_WEBPACK=true``: Skip tests that use Webpack.

Fixing problems automatically
-----------------------------
In any existing Python environment, run ``./bin/fix.py``.
