"""
Provide ``import`` utilities.
"""

from __future__ import annotations

from functools import reduce
from importlib import import_module
from typing import Any


def import_any(fully_qualified_name_: str, /) -> Any:
    """
    Import any symbol in a module by its fully qualified type name.
    """
    try:
        module_name, attrs = fully_qualified_name_.rsplit(":", 1)
        module = import_module(module_name)
        return reduce(getattr, attrs.split("."), module)
    except (AttributeError, ImportError, ValueError):
        raise ImportError(f'Cannot import "{fully_qualified_name_}".') from None


def fully_qualified_name(target: Any, /) -> str:
    """
    Get the fully qualified name of something.
    """
    if not hasattr(target, "__module__") or not hasattr(target, "__qualname__"):
        target = type(target)
    return f"{target.__module__}:{target.__qualname__}"
