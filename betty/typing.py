"""
Providing typing utilities.
"""

from __future__ import annotations

from typing import Any, TypeAlias, TypeVar, final

from betty.classtools import Singleton
from betty.docstring import append

_T = TypeVar("_T")


def _should_mark(target: Any, key: str) -> bool:
    attr_name = f"_betty_typing_{key}"
    if hasattr(target, attr_name):
        return False
    setattr(target, attr_name, True)
    return True


def _internal(target: _T) -> _T:
    if _should_mark(target, "internal"):
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
    if _should_mark(target, "private"):
        target.__doc__ = append(
            target.__doc__ or "",
            "This is private. It **MUST NOT** be used anywhere outside its containing scope.",
        )
    return target


def pickleable(target: _T) -> _T:
    """
    Mark a target as pickleable.
    """
    if _should_mark(target, "pickleable"):
        target.__doc__ = append(
            target.__doc__ or "",
            "This can be pickled.",
        )
    return target


def unpickleable(target: _T) -> _T:
    """
    Mark a target as unpickleable.
    """
    if _should_mark(target, "unpickleable"):
        target.__doc__ = append(
            target.__doc__ or "",
            "This can NOT be pickled, and MUST NOT be used between different processes.",
        )

        def _reduce_ex(*_) -> None:
            raise RuntimeError(f"{target} is not pickleable.")

        target.__reduce_ex__ = _reduce_ex  # type: ignore[assignment, method-assign]
    return target


def threadsafe(target: _T) -> _T:
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


Voidable: TypeAlias = _T | Void
