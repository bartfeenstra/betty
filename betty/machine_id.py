"""
Define portable machine IDs.
"""

from __future__ import annotations

import re
from typing import TypeAlias, TypeGuard

MachineId: TypeAlias = str
"""
A machine ID is a string that meets these criteria:
- At most 250 characters long.
- Lowercase letters, numbers, and hyphens (-).

See :py:func:`betty.machine_id.validate_machine_id`.
"""
_MACHINE_ID_PATTERN = re.compile(r"^[a-z0-9\-]{1,250}$")


def validate_machine_id(alleged_machine_id: str) -> TypeGuard[MachineId]:
    """
    Validate that a string is a machine ID.
    """
    return _MACHINE_ID_PATTERN.fullmatch(alleged_machine_id) is not None
