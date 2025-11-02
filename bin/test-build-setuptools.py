#!/usr/bin/env python
"""
Test the setuptools build.
"""

import sys
from os import path
from subprocess import check_call
from tempfile import TemporaryDirectory

print("Running Setuptools...")  # noqa T201

check_call(["python", path.join("bin", "build-setuptools.py"), "0.0.0"])
wheel_path = "dist/betty-0.0.0-py3-none-any.whl"
venv_bin = "Scripts" if sys.platform.startswith("win32") else "bin"
with TemporaryDirectory() as working_directory_path_str:
    check_call(["python", "-m", "virtualenv", "venv"], cwd=working_directory_path_str)
    check_call(
        [
            path.join(working_directory_path_str, "venv", venv_bin, "pip"),
            "install",
            wheel_path,
        ]
    )
    check_call(
        [path.join(working_directory_path_str, "venv", venv_bin, "betty"), "--version"]
    )

# Remove any stale artifacts.
check_call(["python", path.join("bin", "clean-build.py")])
