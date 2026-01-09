#!/usr/bin/env python
"""
Run ty.
"""

import sys
from subprocess import check_call

print("Running ty...")  # noqa: T201

check_call(["ty", "check", *sys.argv[1:]])
