from importlib import import_module
from typing import Any


def import_any(fully_qualified_type_name: str) -> Any:
    try:
        module_name, type_name = fully_qualified_type_name.rsplit('.', 1)
    except ValueError:
        raise ImportError(f'Cannot import "{fully_qualified_type_name}".')
    try:
        return getattr(import_module(module_name), type_name)
    except (AttributeError, ImportError):
        raise ImportError(f'Cannot import "{fully_qualified_type_name}".')


def fully_qualified_type_name(importable: Any) -> str:
    assert '.' not in importable.__qualname__
    return f'{importable.__module__}.{importable.__qualname__}'
