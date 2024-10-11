"""
Provide ``import`` utilities.
"""

from functools import reduce
from importlib import import_module
from typing import Any


def import_any(fully_qualified_type_name: str) -> Any:
    """
    Import any symbol in a module by its fully qualified type name.
    """
    try:
        if ":" in fully_qualified_type_name:
            module_name, attrs = fully_qualified_type_name.rsplit(":", 1)
            module = import_module(module_name)
            return reduce(getattr, attrs.split("."), module)
        else:
            return import_module(fully_qualified_type_name)
    except (AttributeError, ImportError, ValueError) as error:
        raise ImportError(f'Cannot import "{fully_qualified_type_name}".') from error
