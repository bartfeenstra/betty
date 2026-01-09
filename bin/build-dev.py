#!/usr/bin/env python
"""
Build the development environment.
"""

import sys
from os import path
from subprocess import check_call

check_call([sys.executable, path.join("bin", "build-dev-pip.py")])
check_call([sys.executable, path.join("bin", "build-dev-npm.py")])
