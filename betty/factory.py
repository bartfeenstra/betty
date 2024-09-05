"""
Functionality for creating new class instances.
"""

from __future__ import annotations

from typing import TypeVar, Self


class FactoryError(RuntimeError):
    """
    Raised when a class could not be instantiated by a factory API.
    """

    @classmethod
    def new(cls, new_cls: type) -> Self:
        """
        Create a new instance for a class that failed to instantiate.
        """
        return cls(f"Could not instantiate {new_cls} by calling {new_cls.__name__}()")


_T = TypeVar("_T")


def new(cls: type[_T]) -> _T:
    """
    :raises FactoryError: raised when the class could not be instantiated.
    """
    try:
        return cls()
    except Exception as error:
        raise FactoryError.new(cls) from error
