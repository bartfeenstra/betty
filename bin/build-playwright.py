#!/usr/bin/env python
"""
Install Playwright browser dependencies.
"""

from subprocess import check_call

check_call(["playwright", "install", "--with-deps"])
