#!/usr/bin/env python
"""
Run the tests.
"""

import sys
from os import environ, path
from subprocess import check_call

check_call([sys.executable, path.join("bin", "clean-build.py")])
if "BETTY_TEST_SKIP_RUFF" not in environ or not environ["BETTY_TEST_SKIP_RUFF"]:
    check_call([sys.executable, path.join("bin", "test-ruff.py")])
check_call([sys.executable, path.join("bin", "test-ty.py")])
check_call([sys.executable, path.join("bin", "test-slotscheck.py")])
if (
    "BETTY_TEST_SKIP_STYLELINT" not in environ
    or not environ["BETTY_TEST_SKIP_STYLELINT"]
):
    check_call([sys.executable, path.join("bin", "test-stylelint.py")])
if "BETTY_TEST_SKIP_TSC" not in environ or not environ["BETTY_TEST_SKIP_TSC"]:
    check_call([sys.executable, path.join("bin", "test-tsc.py")])
if "BETTY_TEST_SKIP_ESLINT" not in environ or not environ["BETTY_TEST_SKIP_ESLINT"]:
    check_call([sys.executable, path.join("bin", "test-eslint.py")])
check_call([sys.executable, path.join("bin", "test-pytest.py")])
check_call([sys.executable, path.join("bin", "test-build-package.py")])
