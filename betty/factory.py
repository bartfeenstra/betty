"""
Functionality for creating new class instances.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Self, TypeAlias, cast

from typing_extensions import TypeVar

from betty.asyncio import ensure_await

if TYPE_CHECKING:
    from betty.service.level.factory import AnyFactoryTarget

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
    type[SelfFactory] | type[_T] | Callable[[], Awaitable[_T]] | Callable[[], _T]
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


async def new_target(target: AnyFactoryTarget[_T], /) -> _T:
    """
    Create a new instance.

    :raises FactoryError: raised when ``target`` could not be instantiated.
    """
    try:
        if isinstance(target, type):
            if issubclass(target, SelfFactory):
                return cast(_T, await target.new())
            return cast(type[_T], target)()
        if callable(target):
            return await ensure_await(target())
        raise FactoryError(target)
    except Exception as error:
        raise FactoryError(target) from error
