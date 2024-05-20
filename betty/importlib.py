"""
Provide ``import`` utilities.
"""

from importlib import import_module
from typing import Any


def import_any(fully_qualified_type_name: str) -> Any:
    """
    Import any symbol by its fully qualified type name.
    """
    try:
        module_name, type_name = fully_qualified_type_name.rsplit(".", 1)
    except ValueError:
        raise ImportError(f'Cannot import "{fully_qualified_type_name}".') from None
    try:
        return getattr(import_module(module_name), type_name)
    except (AttributeError, ImportError):
        raise ImportError(f'Cannot import "{fully_qualified_type_name}".') from None


def fully_qualified_type_name(importable: Any) -> str:
    """
    Get the fully qualified name for a type.
    """
    assert "." not in importable.__qualname__
    return f"{importable.__module__}.{importable.__qualname__}"
