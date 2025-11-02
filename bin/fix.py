#!/usr/bin/env python
"""
Automatically fix as many problems as possible.
"""

from subprocess import check_call

# Fix Python code style violations.
check_call(["ruff", "check", "--fix", "."])
check_call(["ruff", "format", "."])

# Fix CSS code style violations.
check_call(
    ["node_modules/.bin/stylelint", "--fix", "betty/**/*.css", "betty/**/*.scss"]
)

# Fix JS code style violations.
check_call(
    ["node_modules/.bin/eslint", "--fix", "-c", "eslint.config.js", "betty", "js"]
)
