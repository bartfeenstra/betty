"""
The 'nothing' type.
"""

from __future__ import annotations

from typing import final


class _NothingMeta(type):
    def __bool__(self):
        return False

    def __repr__(cls):
        return f"<{Nothing.__name__}>"


@final
class Nothing(metaclass=_NothingMeta):
    """
    A sentinel that describes the absence of a value.

    Using this sentinel allows for actual values to be ``None``. Like ``None``,
    ``Nothing`` is only ever used through its type, and never instantiated.
    """

    def __new__(cls):  # noqa: D102
        raise TypeError(f"{cls.__name__} cannot be initialized.")


type NothingType = type[Nothing]
