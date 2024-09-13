"""
Functionality for creating new class instances.
"""

from __future__ import annotations

from abc import abstractmethod, ABC
from collections.abc import Callable, Awaitable
from typing import TypeVar, Self, Generic, TypeAlias


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


async def new(cls: type[_T]) -> _T:
    """
    Create a new instance.

    :raises FactoryError: raised when the class could not be instantiated.
    """
    try:
        return cls()
    except Exception as error:
        raise FactoryError.new(cls) from error


class DependentFactory(ABC, Generic[_T]):
    """
    Provide a factory for classes that depend on ``self``.
    """

    @abstractmethod
    async def new(self, cls: type[_T]) -> _T:
        """
        Create a new instance.

        :raises FactoryError: raised when the class could not be instantiated.
        """
        pass


Factory: TypeAlias = Callable[[type[_T]], Awaitable[_T]]
