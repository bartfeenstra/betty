from importlib import import_module
from typing import Any


def import_any(fully_qualified_type_name: str) -> Any:
    try:
        module_name, type_name = fully_qualified_type_name.rsplit('.', 1)
        return getattr(import_module(module_name), type_name)
    except (AttributeError, ValueError):
        raise ImportError('Cannot import "%s".' % fully_qualified_type_name)
