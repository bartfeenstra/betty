#!/usr/bin/env python
"""
Run Ruff.
"""

from subprocess import check_call

print("Running Ruff...")  # noqa T201

check_call(["ruff", "check", "."])
check_call(["ruff", "format", "--check", "."])
