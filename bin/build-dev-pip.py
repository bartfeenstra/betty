#!/usr/bin/env python
"""
Install Python dependencies.
"""

from os import path
from subprocess import check_call

check_call(["pip", "install", "-e", ".[development]"])
check_call(["python", path.join("bin", "build-playwright.py")])
