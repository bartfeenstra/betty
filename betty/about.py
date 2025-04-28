"""Provide information about (this version of) Betty."""

from __future__ import annotations

import platform
import sys
from importlib import metadata
from typing import TYPE_CHECKING

DEV_VERSION = "0.0.0"

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping


def version() -> str:
    """
    Get the current Betty installation's version, if it has any.
    """
    return metadata.version("betty")


def version_label() -> str:
    """
    Get the human-readable label for the current Betty installation's version.
    """
    return "development" if is_development() else version()


def is_stable() -> bool:
    """
    Check if the current Betty installation is a stable version.
    """
    return version() != DEV_VERSION


def is_development() -> bool:
    """
    Check if the current Betty installation is an unstable development version.
    """
    return version() == DEV_VERSION


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


def report() -> str:
    """
    Produce a human-readable report about the current Betty installation.

    :returns: A human-readable string in US English, using monospace indentation.
    """
    return _indent_mapping(
        {
            "Betty": version_label(),
            "Operating system": platform.platform(),
            "Python": sys.version,
            "Python packages": _indent_mapping(
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
