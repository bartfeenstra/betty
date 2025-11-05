#!/usr/bin/env python
"""
Build packages using setuptools.
"""

import re
import sys
from os import path
from subprocess import check_call

if len(sys.argv) != 2:
    raise RuntimeError(
        "This command takes a single argument, which is the version to release."
    )
VERSION = sys.argv[1]

# Temporarily update pyproject.toml with the build version.
with open("pyproject.toml") as f:
    original_pyproject = f.read()
versioned_pyproject = re.sub(
    r"^version = '0.0.0'$",
    f"version = '{VERSION}'",
    original_pyproject,
    flags=re.MULTILINE,
)
with open("pyproject.toml", mode="w") as f:
    f.write(versioned_pyproject)

try:
    # Install Python dependencies.
    check_call(["pip", "install", "-e", ".[setuptools]"])

    # Prepare the workspace directories.
    check_call(["python", path.join("bin", "clean-build.py")])

    # Build the package.
    check_call(["python", "-m", "build"])
    check_call(["twine", "check", "dist/*"])
finally:
    # Clean up.
    with open("pyproject.toml", mode="w") as f:
        f.write(original_pyproject)
