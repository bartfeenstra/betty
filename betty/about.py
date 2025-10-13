"""Provide information about (this version of) Betty."""

from __future__ import annotations

from importlib import metadata

_DEV_VERSION = "0.0.0"


VERSION = metadata.version("betty")
"""
The current Betty installation's version.
"""

_VERSION_MAJOR_PARTS = VERSION.split(".")
VERSION_MAJOR = (
    f"0.{_VERSION_MAJOR_PARTS[1]}"
    if _VERSION_MAJOR_PARTS[0] == "0"
    else _VERSION_MAJOR_PARTS[0]
)
"""
The current Betty installation's major version.

Use this instead of :py:const:`betty.about.VERSION` in public situations, where we do not want to include minor version
information because that may disclose security issues.
"""


IS_STABLE = VERSION != _DEV_VERSION
"""
Whether the current Betty installation is a stable version.
"""


IS_DEVELOPMENT = not IS_STABLE
"""
Whether the current Betty installation is an unstable development version.
"""


VERSION_LABEL = "development" if IS_DEVELOPMENT else VERSION
"""
The human-readable label for the current Betty installation's version.
"""


VERSION_MAJOR_LABEL = "development" if IS_DEVELOPMENT else VERSION_MAJOR
"""
The human-readable label for the current Betty installation's major version.

Use this instead of :py:const:`betty.about.VERSION_LABEL` in public situations, where we do not want to include minor
version information because that may disclose security issues.
"""
