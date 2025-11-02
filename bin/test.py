#!/usr/bin/env python
"""
Run the tests.
"""

from os import environ, path
from subprocess import check_call

check_call(["python", path.join("bin", "clean-build.py")])
if "BETTY_TEST_SKIP_RUFF" not in environ or not environ["BETTY_TEST_SKIP_RUFF"]:
    check_call(["python", path.join("bin", "test-ruff.py")])
if "BETTY_TEST_SKIP_MYPY" not in environ or not environ["BETTY_TEST_SKIP_MYPY"]:
    check_call(["python", path.join("bin", "test-mypy.py")])
if (
    "BETTY_TEST_SKIP_STYLELINT" not in environ
    or not environ["BETTY_TEST_SKIP_STYLELINT"]
):
    check_call(["python", path.join("bin", "test-stylelint.py")])
if "BETTY_TEST_SKIP_TSC" not in environ or not environ["BETTY_TEST_SKIP_TSC"]:
    check_call(["python", path.join("bin", "test-tsc.py")])
if "BETTY_TEST_SKIP_ESLINT" not in environ or not environ["BETTY_TEST_SKIP_ESLINT"]:
    check_call(["python", path.join("bin", "test-eslint.py")])
check_call(["python", path.join("bin", "test-pytest.py")])
check_call(["python", path.join("bin", "test-build-setuptools.py")])
