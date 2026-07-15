"""Provide information about (this version of) Betty."""

from __future__ import annotations

from importlib import metadata
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence

_dev_version: Final[str] = "0.0.0"


version: Final[str] = metadata.version("betty")
"""
The current Betty installation's version.
"""

_version_major_parts: Final[Sequence[str]] = version.split(".")
version_major: Final[str] = (
    f"0.{_version_major_parts[1]}"
    if _version_major_parts[0] == "0"
    else _version_major_parts[0]
)
"""
The current Betty installation's major version.

Use this instead of :py:const:`betty.about.VERSION` in public situations, where we do not want to include minor version
information because that may disclose security issues.
"""


is_stable: Final[bool] = version != _dev_version
"""
Whether the current Betty installation is a stable version.
"""


is_development: Final[bool] = not is_stable
"""
Whether the current Betty installation is an unstable development version.
"""


version_label: Final[str] = "development" if is_development else version
"""
The human-readable label for the current Betty installation's version.
"""


version_major_label: Final[str] = "development" if is_development else version_major
"""
The human-readable label for the current Betty installation's major version.

Use this instead of :py:const:`betty.about.VERSION_LABEL` in public situations, where we do not want to include minor
version information because that may disclose security issues.
"""

url_code: Final[str] = "https://github.com/bartfeenstra/betty"
"""
The URL to the source code.
"""

url_documentation: Final[str] = "https://betty.readthedocs.io"
"""
The URL to the documentation.
"""

url_report_issue: Final[str] = "https://github.com/bartfeenstra/betty/issues/new"
"""
The URL to report an issue with Betty.
"""

url: Final[str] = url_documentation
"""
The main, generic URL to Betty on the web.
"""
