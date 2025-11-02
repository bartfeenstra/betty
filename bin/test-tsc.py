#!/usr/bin/env python
"""
Run tsc.
"""

from subprocess import check_call

print("Running tsc...")  # noqa T201

check_call(["node_modules/.bin/tsc", "--noEmit", "--allowImportingTsExtensions"])
