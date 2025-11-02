#!/usr/bin/env python
"""
Build the development environment.
"""

from os import path
from subprocess import check_call

check_call(["python", path.join("bin", "build-dev-pip.py")])
check_call(["python", path.join("bin", "build-dev-npm.py")])
