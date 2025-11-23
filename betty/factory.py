"""
Functionality for creating new class instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, Self, TypeAlias, cast

from typing_extensions import TypeVar

from betty.asyncio import ensure_await

_T = TypeVar("_T", default=Any)


class IndependentFactory(ABC):
    """
    Provide a factory for classes that can instantiate themselves asynchronously.
    """

    @classmethod
    @abstractmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """


Target: TypeAlias = (
    type[IndependentFactory] | type[_T] | Callable[[], Awaitable[_T]] | Callable[[], _T]
)
"""
#. If ``target`` subclasses :py:class:`betty.factory.IndependentFactory`, this will call return ``target``'s
   ``new()``'s return value.
#. Else, if ``target`` is a class, ``target()`` will be called without arguments, and the resulting
   instance will be returned.
#. Else, ``target`` is called as a function. If its return value is an :py:class:`collections.Awaitable`,
   it is awaited and then returned. Otherwise, the return value is returned directly.
"""


class FactoryError(RuntimeError):
    """
    Raised when a class could not be instantiated by a factory API.
    """

    def __init__(self, target: Target, /):
        super().__init__(f"Could not instantiate {repr(target)}")


async def new(target: Target[_T], /) -> _T:
    """
    Create a new instance.

    :raises FactoryError: raised when ``target`` could not be instantiated.
    """
    try:
        if isinstance(target, type):
            if issubclass(target, IndependentFactory):
                return cast(_T, await target.new())
            return cast(type[_T], target)()
        return await ensure_await(target())
    except Exception as error:
        raise FactoryError(target) from error


class TargetFactory(ABC):
    """
    Provide a factory for classes that depend on ``self``.
    """

    @abstractmethod
    async def new_target(self, target: Target[_T], /) -> _T:
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be called.
        """


class Factory(Protocol):
    """
    A callable to create a new instance.
    """

    async def __call__(self, target: Target[_T], /) -> _T:
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be instantiated.
        """
