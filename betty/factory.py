"""
Functionality for creating new class instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Never, Self, TypeAlias, overload

from typing_extensions import TypeVar

from betty.asyncio import resolve_await

_T = TypeVar("_T")


class SelfFactory(ABC):
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
    type[SelfFactory] | Callable[[], Awaitable[_T]] | Callable[[], _T] | Any
)
"""
#. If ``target`` subclasses :py:class:`betty.factory.SelfFactory`, this will return ``target``'s
   ``new()``'s return value.
#. Else, if ``target`` is a class, ``target()`` will be called without arguments, and the resulting
   instance will be returned.
#. Else, ``target`` is called as a function. If its return value is an :py:class:`collections.Awaitable`,
   it is awaited and then returned. Otherwise, the return value is returned directly.
"""


class FactoryError(Exception):
    """
    Raised when a class could not be instantiated.
    """


@overload
async def new_target(target: Target[_T], /) -> _T:
    pass


@overload
async def new_target(target: Any, /) -> Never:
    pass


async def new_target(target):
    """
    Create a new instance.

    :raises FactoryError: raised when ``target`` could not be instantiated.
    """
    try:
        if isinstance(target, type) and issubclass(target, SelfFactory):
            return await target.new()
        if callable(target):
            return await resolve_await(target())
        raise FactoryError(target)
    except Exception as error:
        raise FactoryError(target) from error
