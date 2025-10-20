"""Provide information about (this version of) Betty."""

from __future__ import annotations

import platform
import sys
from importlib import metadata
from typing import TYPE_CHECKING

_DEV_VERSION = "0.0.0"

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from betty.locale.localizer import Localizer


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


def _indent_mapping(items: Mapping[str, str]) -> str:
    max_indentation = max(map(len, items.keys())) + 4
    return "\n".join(
        "\n".join(_indent_mapping_item(x[0], x[1], max_indentation))
        for x in items.items()
    )


def _indent_mapping_item(key: str, value: str, max_indentation: int) -> Iterator[str]:
    lines = value.split("\n")
    yield f"{key}{' ' * (max_indentation - len(key))}    {lines[0]}"
    for line in lines[1:]:
        yield f"{' ' * max_indentation}    {line}"


def report(*, localizer: Localizer) -> str:
    """
    Produce a human-readable report about the current Betty installation.

    :returns: A human-readable string in US English, using monospace indentation.
    """
    return _indent_mapping(
        {
            "Betty": VERSION_LABEL,
            localizer._("Operating system"): platform.platform(),
            "Python": sys.version,
            localizer._("Python packages"): _indent_mapping(
                {
                    x.metadata["Name"]: x.version
                    for x in sorted(
                        metadata.distributions(),
                        key=lambda x: x.metadata["Name"].lower(),  # type: ignore[no-any-return, unused-ignore]
                    )
                }
            ),
        }
    )
