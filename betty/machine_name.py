"""
Define portable machine names.
"""

from __future__ import annotations

import re
from typing import TypeAlias, TypeGuard

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
