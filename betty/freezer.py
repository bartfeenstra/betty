"""
The freezer API.

This API provides tools to build cooperative and conditional (im)mutability.
"""

from __future__ import annotations

from typing import Any


class Frozen:
    """
    An object that is frozen (immutable) after creation.
    """


def is_frozen(value: Any) -> bool:
    """
    Check if a value is frozen (immutable) and must not be changed.
    """
    return isinstance(value, Frozen)
