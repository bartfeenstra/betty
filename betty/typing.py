"""
Providing typing utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from betty.docstring import append

if TYPE_CHECKING:
    from ty_extensions import Intersection
else:

    class Intersection:
        """
        A fake intersection type that works runtime, until https://github.com/astral-sh/ty/issues/2084 is fixed.
        """

        def __class_getitem__(cls, item: Any):
            pass  # pragma: nocover


def _should_mark(target: Any, key: str, /) -> bool:
    attr_name = f"_betty_typing_{key}"
    if hasattr(target, attr_name):
        return False
    setattr(target, attr_name, True)
    return True


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
class Void:
    """
    A sentinel that describes the absence of a value.

    Using this sentinel allows for actual values to be ``None``. Like ``None``,
    ``Void`` is only ever used through its type, and never instantiated.
    """

    def __new__():  # noqa: D102
        raise NotImplementedError


type VoidType = type[Void]
