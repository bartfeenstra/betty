#!/usr/bin/env python
"""
Test the setuptools build.
"""

import sys
from os import path
from subprocess import check_call, check_output
from tempfile import TemporaryDirectory

print("Running Setuptools...")  # noqa: T201

VERSION = "0.0.0a0"
check_call([sys.executable, path.join("bin", "build-package.py"), VERSION])
wheel_path = f"dist/betty-{VERSION}-py3-none-any.whl"
venv_bin = "Scripts" if sys.platform.startswith("win32") else "bin"
with TemporaryDirectory() as working_directory_path_str:
    check_call(
        [sys.executable, "-m", "virtualenv", "venv"], cwd=working_directory_path_str
    )
    check_call(
        [
            path.join(working_directory_path_str, "venv", venv_bin, "pip"),
            "install",
            wheel_path,
        ]
    )
    output = check_output(
        [path.join(working_directory_path_str, "venv", venv_bin, "betty"), "about"]
    ).decode(sys.stdout.encoding)
    assert VERSION in output

# Remove any stale artifacts.
check_call([sys.executable, path.join("bin", "clean-build.py")])
