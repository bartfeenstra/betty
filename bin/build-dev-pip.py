#!/usr/bin/env python
"""
Install Python dependencies.
"""

import sys
from os import path
from subprocess import check_call

check_call(["pip", "install", "-e", ".[development]"])
check_call([sys.executable, path.join("bin", "build-playwright.py")])
