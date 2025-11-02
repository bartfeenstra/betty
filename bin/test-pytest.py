#!/usr/bin/env python
"""
Run pytest.
"""

import sys
from os import environ
from subprocess import check_call

print("Running pytest...")  # noqa T201

check_call(["coverage", "erase"])
check_call(
    ["coverage", "run", "--module", "pytest", *sys.argv[2:]],
    env={
        **environ,
        "COVERAGE_PROCESS_START": "$(pwd)/.coveragerc",
        "PYTHONPATH": "$(cd site; pwd)",
    },
)
check_call(["coverage", "combine"])
check_call(["coverage", "report", "--skip-covered", "--skip-empty"])
