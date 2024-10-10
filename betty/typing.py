"""
Providing typing utilities.
"""

from __future__ import annotations

from typing import TypeVar, TypeAlias

from betty.docstring import append

_T = TypeVar("_T")


def _internal(target: _T) -> _T:
    target.__doc__ = append(
        target.__doc__ or "",
        "This is internal. It **MAY** be used anywhere in Betty's source code, but **MUST NOT** be used by third-party code.",
    )
    return target


@_internal
def internal(target: _T) -> _T:
    """
    Mark a target as internal to Betty.

    Anything decorated with ``@internal`` MAY be used anywhere in Betty's source code,
    but MUST be considered private by third-party code.
    """
    return _internal(target)


@internal
def public(target: _T) -> _T:
    """
    Mark a target as publicly usable.

    This is intended for items nested inside something marked with :py:func:`betty.typing.internal`,
    such as class attributes: third-party code **SHOULD NOT** use a class marked ``@internal``
    directly, but **MAY** use any of its attributes that are marked ``@public``.
    """
    return target


def private(target: _T) -> _T:
    """
    Mark a target as private to its containing scope.

    This is intended for items that cannot be marked private by prefixing their names with an underscore.
    """
    target.__doc__ = append(
        target.__doc__ or "",
        "This is private. It **MUST NOT** be used anywhere outside its containing scope.",
    )
    return target


def threadsafe(target: _T) -> _T:
    """
    Mark a target as thread-safe.
    """
    target.__doc__ = append(
        target.__doc__ or "",
        "This is thread-safe, which means you can safely use this between different threads.",
    )
    return target


class Void:
    """
    A sentinel that describes the absence of a value.

    Using this sentinel allows for actual values to be ``None``. Like ``None``,
    ``Void`` is only ever used through its type, and never instantiated.
    """

    def __new__(cls):  # pragma: no cover  # noqa D102
        raise RuntimeError("The Void sentinel cannot be instantiated.")


Voidable: TypeAlias = _T | type[Void]
