"""
Providing typing utilities.
"""

from __future__ import annotations

from typing import Any, final

from betty.classtools import Singleton
from betty.docstring import append


def _should_mark(target: Any, key: str, /) -> bool:
    attr_name = f"_betty_typing_{key}"
    if hasattr(target, attr_name):
        return False
    setattr(target, attr_name, True)
    return True


def _internal[T](target: T, /) -> T:
    if _should_mark(target, "internal"):
        target.__doc__ = append(
            target.__doc__ or "",
            "This is internal. It **MAY** be used anywhere in Betty's source code, but **MUST NOT** be used by third-party code.",
        )
    return target


@_internal
def internal[T](target: T, /) -> T:
    """
    Mark a target as internal to Betty.

    Anything decorated with ``@internal`` MAY be used anywhere in Betty's source code,
    but MUST be considered private by third-party code.
    """
    return _internal(target)


@internal
def public[T](target: T, /) -> T:
    """
    Mark a target as publicly usable.

    This is intended for items nested inside something marked with :py:func:`betty.typing.internal`,
    such as class attributes: third-party code **SHOULD NOT** use a class marked ``@internal``
    directly, but **MAY** use any of its attributes that are marked ``@public``.
    """
    return target


def private[T](target: T, /) -> T:
    """
    Mark a target as private to its containing scope.

    This is intended for items that cannot be marked private by prefixing their names with an underscore.
    """
    if _should_mark(target, "private"):
        target.__doc__ = append(
            target.__doc__ or "",
            "This is private. It **MUST NOT** be used anywhere outside its containing scope.",
        )
    return target


def threadsafe[T](target: T, /) -> T:
    """
    Mark a target as thread-safe.
    """
    if _should_mark(target, "threadsafe"):
        target.__doc__ = append(
            target.__doc__ or "",
            "This is thread-safe, which means you can safely use this between different threads.",
        )
    return target


@final
class Void(Singleton):
    """
    A sentinel that describes the absence of a value.

    Using this sentinel allows for actual values to be ``None``. Like ``None``,
    ``Void`` is only ever used through its type, and never instantiated.
    """
