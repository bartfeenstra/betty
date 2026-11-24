"""
Provide ``import`` utilities.
"""

from __future__ import annotations

from typing import Any


def fully_qualified_name(target: Any, /) -> str:
    """
    Get the fully qualified name of something.
    """
    if not hasattr(target, "__module__") or not hasattr(target, "__qualname__"):
        target = type(target)
    return f"{target.__module__}:{target.__qualname__}"
