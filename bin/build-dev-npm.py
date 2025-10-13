#!/usr/bin/env python
"""
Install JavaScript dependencies.
"""

import sys
from subprocess import STDOUT, check_call, check_output

is_windows = shell = sys.platform.startswith("win32")
check_call(["npm", "install"], shell=is_windows)
node_version = (
    check_output(
        ["node", "-e", r"console.log(process.versions.node.split('.')[0])"],
        stderr=STDOUT,
    )
    .decode(sys.stdout.encoding)
    .strip()
)
check_call(
    ["npm", "install", "--no-save", f"@types/node@{node_version}"], shell=is_windows
)
