#!/usr/bin/env python
"""
Run pytest.
"""

import sys
from os import environ, getcwd, path
from subprocess import check_call

print("Running pytest...")  # noqa T201

check_call(["coverage", "erase"])
check_call(
    ["coverage", "run", "--module", "pytest", "-n", "auto", *sys.argv[1:]],
    env={
        **environ,
        "COVERAGE_PROCESS_START": path.join(getcwd(), ".coveragerc"),
        "PYTHONPATH": path.join(getcwd(), "site"),
    },
)
check_call(["coverage", "combine"])
check_call(["coverage", "report", "--skip-covered", "--skip-empty"])
