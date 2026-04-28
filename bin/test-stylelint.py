#!/usr/bin/env python
"""
Run Stylelint.
"""

from subprocess import check_call

print("Running Stylelint...")  # noqa: T201

check_call(["node_modules/.bin/stylelint", "data/**/*.css", "data/**/*.scss"])
