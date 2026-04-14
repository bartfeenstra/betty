#!/usr/bin/env python
"""
Run Ruff.
"""

from subprocess import check_call

print("Running Ruff...")  # noqa: T201

check_call(["ruff", "check", "--preview", "."])
check_call(["ruff", "format", "--preview", "--check", "."])
