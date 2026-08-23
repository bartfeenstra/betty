#!/usr/bin/env python
"""
Run slotscheck.
"""

import sys
from subprocess import check_call

print("Running slotscheck...")  # noqa: T201

check_call([
    "slotscheck",
    "-v",
    "-m",
    "betty",
    "--exclude-modules",
    r"betty\.tests",
    "--exclude-modules",
    r"betty\.test_utils",
    "--require-superclass",
    *sys.argv[1:],
])
