#!/usr/bin/env python
"""
Run ESLint.
"""

import sys
from subprocess import check_call

print("Running ESLint...")  # noqa: T201

check_call([
    "node_modules/.bin/eslint",
    "-c",
    "eslint.config.ts",
    "data",
    "eslint.config.ts",
    *sys.argv[1:],
])
