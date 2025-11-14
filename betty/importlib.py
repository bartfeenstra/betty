"""
Provide ``import`` utilities.
"""

from functools import reduce
from importlib import import_module
from typing import Any


def import_any(fully_qualified_name: str) -> Any:
    """
    Import any symbol in a module by its fully qualified type name.
    """
    try:
        module_name, attrs = fully_qualified_name.rsplit(":", 1)
        module = import_module(module_name)
        return reduce(
            getattr,  # type: ignore[arg-type]
            attrs.split("."),
            module,
        )
    except (AttributeError, ImportError, ValueError):
        raise ImportError(f'Cannot import "{fully_qualified_name}".') from None


def fully_qualified_name(target: Any) -> str:
    """
    Get the fully qualified name of something.
    """
    return f"{target.__module__}:{target.__qualname__}"
