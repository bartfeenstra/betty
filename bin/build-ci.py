#!/usr/bin/env python
"""
Build the CI environment.

This command is internal to Betty's own CI setup.
"""

import sys
from os import environ, path
from subprocess import check_call

check_call(["pip", "install", ".[ci]"])
check_call([sys.executable, path.join("bin", "build-dev-npm.py")])
if (
    "BETTY_TEST_SKIP_PLAYWRIGHT" not in environ
    or not environ["BETTY_TEST_SKIP_PLAYWRIGHT"]
):
    check_call(["playwright", "install"])
