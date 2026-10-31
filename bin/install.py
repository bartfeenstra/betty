#!/usr/bin/env python
"""
Install a Betty development environment.
"""

import sys
from argparse import ArgumentParser
from subprocess import STDOUT, check_call, check_output


def _main() -> None:
    parser = ArgumentParser(description="Install a Betty development environment.")
    parser.add_argument(
        "--no-pip",
        dest="__pip",
        action="store_false",
        default=True,
        help="Do not (re)install pip",
    )
    parser.add_argument(
        "--no-npm",
        dest="__npm",
        action="store_false",
        default=True,
        help="Do not (re)install npm",
    )
    parser.add_argument(
        "--no-playwright",
        dest="__playwright",
        action="store_false",
        default=True,
        help="Do not (re)install Playwright browsers and their system dependencies",
    )

    namespace = parser.parse_args()
    pip = namespace.__pip
    npm = namespace.__npm
    playwright = namespace.__playwright and pip

    if pip:
        _install_pip()
    if playwright:
        _install_playwright()
    if npm:
        _install_npm()


def _install_pip() -> None:
    check_call(["pip", "install", "-e", ".[dev]"])


def _install_npm() -> None:
    is_windows = sys.platform.startswith("win32")
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


def _install_playwright() -> None:
    check_call(["playwright", "install", "--with-deps"])


if __name__ == "__main__":
    _main()
