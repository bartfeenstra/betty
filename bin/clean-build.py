#!/usr/bin/env python
"""
Clean all package build artifacts.
"""

from contextlib import suppress
from shutil import rmtree

with suppress(FileNotFoundError):
    rmtree("build")
with suppress(FileNotFoundError):
    rmtree("dist")
with suppress(FileNotFoundError):
    rmtree("betty.egg-info")
