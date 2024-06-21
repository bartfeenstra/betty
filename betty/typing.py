"""
Providing typing utilities.
"""

from typing import TypeVar


_T = TypeVar("_T")


def internal(target: _T) -> _T:
    """
    Mark a target as internal to Betty.

    Anything decorated with ``@internal`` MAY be used anywhere in Betty's source code,
    but MUST be considered private by third-party code.

    This function is internal (and ironically cannot be decorated with itself).
    """
    return target
