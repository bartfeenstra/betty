"""
Requirements for services.
"""

from __future__ import annotations

from functools import partial, update_wrapper
from typing import (
    TYPE_CHECKING,
    Concatenate,
    Generic,
    ParamSpec,
    TypeVar,
    final,
    overload,
)

from betty.asyncio import resolve_await
from betty.exception import HumanFacingException
from betty.importlib import fully_qualified_name
from betty.service.level import ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

_RequirementT = TypeVar("_RequirementT")
_ReturnT = TypeVar("_ReturnT")
_MagicT = TypeVar("_MagicT")
_P = ParamSpec("_P")


@final
class Requirement(Generic[_RequirementT]):
    """
    A service level requirement.
    """

    def __init__(
        self, require: Callable[[ServiceLevel, str], Awaitable[_RequirementT]], /
    ):

        self._require = require

    @overload
    def __call__(self, f: ServiceLevel, /) -> Awaitable[_RequirementT]:
        pass

    @overload
    def __call__(
        self,
        f: Callable[Concatenate[_RequirementT, _P], Awaitable[_ReturnT] | _ReturnT],
    ) -> Callable[Concatenate[ServiceLevel, _P], Awaitable[_ReturnT]]:
        pass

    @overload
    def __call__(
        self,
        f: Callable[
            Concatenate[_MagicT, _RequirementT, _P], Awaitable[_ReturnT] | _ReturnT
        ],
    ) -> Callable[Concatenate[_MagicT, ServiceLevel, _P], Awaitable[_ReturnT]]:
        pass

    def __call__(
        self, f
    ) -> CallableRequirement[_RequirementT, _P, _ReturnT] | Awaitable[_RequirementT]:
        """
        Decorate a callable with this requirement.
        """
        if isinstance(f, ServiceLevel):
            return self._require(f, "**UNKNOWN**")
        return CallableRequirement(self._require, f)


@final
class CallableRequirement(Generic[_RequirementT, _P, _ReturnT]):
    """
    A requirement that can be called or used as a descriptor.
    """

    def __init__(
        self,
        require: Callable[[ServiceLevel, str], Awaitable[_RequirementT]],
        f: Callable[Concatenate[_RequirementT, _P], Awaitable[_ReturnT] | _ReturnT]
        | Callable[
            Concatenate[_MagicT, _RequirementT, _P], Awaitable[_ReturnT] | _ReturnT
        ],
    ):
        self._require = require
        update_wrapper(self, f)
        self._f = f

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(self, instance)

    @overload
    async def __call__(
        self, requirement: _RequirementT, *args: _P.args, **kwargs: _P.kwargs
    ) -> _ReturnT:
        pass

    @overload
    async def __call__(
        self,
        magic: _MagicT,
        requirement: _RequirementT,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _ReturnT:
        pass

    async def __call__(self, *args, **kwargs) -> _ReturnT:
        """
        Call the decorated callable.
        """
        index = 0 if isinstance(args[0], ServiceLevel) else 1
        return await resolve_await(
            self._f(
                *args[:index],
                await self._require(args[index], fully_qualified_name(self._f)),
                *args[index + 1 :],
                **kwargs,
            )
        )


@final
class UnmetRequirement(HumanFacingException):
    """
    Raised when a requirement is not met.
    """
