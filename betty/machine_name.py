"""
Define portable machine names.
"""

from __future__ import annotations

import re
from typing import Any, TypeAlias, TypeGuard

from betty.assertion import AssertionChain, assert_str
from betty.exception import HumanFacingException
from betty.locale.localizable import _

MachineName: TypeAlias = str
"""
A machine name is a string that meets these criteria:
- At most 250 characters long.
- Lowercase letters, numbers, and hyphens (-).

See :py:func:`betty.machine_name.validate_machine_name`.
"""


_MACHINE_NAME_PATTERN = re.compile(r"^[a-z0-9\-]{1,250}$")


def validate_machine_name(alleged_machine_name: str) -> TypeGuard[MachineName]:
    """
    Validate that a string is a machine name.
    """
    return _MACHINE_NAME_PATTERN.fullmatch(alleged_machine_name) is not None


class InvalidMachineName(HumanFacingException, ValueError):
    """
    Raised when something is not a valid machine name.
    """

    def __init__(self, value: str, /):
        super().__init__(
            _(
                '"{value}" is not a valid machine name: only lowercase letters, digits, and hyphens (-) are allowed.'
            ).format(value=value)
        )


def assert_machine_name() -> AssertionChain[Any, MachineName]:
    """
    Assert that something is a machine name.
    """

    def _assert(value: Any) -> MachineName:
        if not validate_machine_name(value):
            raise InvalidMachineName(value)
        return value

    return assert_str() | _assert


_MACHINIFY_DISALLOWED_CHARACTER_PATTERN = re.compile(r"[^a-z0-9\-]")
_MACHINIFY_HYPHEN_PATTERN = re.compile(r"-{2,}")


def machinify(source: str) -> MachineName | None:
    """
    Attempt to convert a source string into a valid machine name.
    """
    return (
        _MACHINIFY_HYPHEN_PATTERN.sub(
            "-", _MACHINIFY_DISALLOWED_CHARACTER_PATTERN.sub("-", source.lower())
        ).strip("-")[:250]
        or None
    )
