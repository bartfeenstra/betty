#!/usr/bin/env python
"""
Run mypy.
"""

import sys
from subprocess import check_call

print("Running mypy...")  # noqa T201

check_call(["mypy", *sys.argv[2:]])
