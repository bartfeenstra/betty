"""
Requirements for services.
"""

from __future__ import annotations

from functools import partial, update_wrapper
from typing import TYPE_CHECKING, Any, Concatenate, final, overload

from betty.asyncio import resolve_await
from betty.exception import HumanFacingException
from betty.importlib import fully_qualified_name
from betty.service.level import ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


@final
class Requirement[RequirementT]:
    """
    A service level requirement.
    """

    def __init__(
        self, require: Callable[[ServiceLevel, str], Awaitable[RequirementT]], /
    ):

        self._require = require

    @overload
    def __call__(self, f: ServiceLevel, /) -> Awaitable[RequirementT]:
        pass

    @overload
    def __call__[**P, ReturnT](
        self,
        f: Callable[Concatenate[RequirementT, P], Awaitable[ReturnT] | ReturnT],
    ) -> Callable[Concatenate[ServiceLevel, P], Awaitable[ReturnT]]:
        pass

    @overload
    def __call__[**P, ReturnT, MagicT](
        self,
        f: Callable[Concatenate[MagicT, RequirementT, P], Awaitable[ReturnT] | ReturnT],
    ) -> Callable[Concatenate[MagicT, ServiceLevel, P], Awaitable[ReturnT]]:
        pass

    def __call__[**P, ReturnT](
        self, f
    ) -> CallableRequirement[RequirementT, P, ReturnT] | Awaitable[RequirementT]:
        """
        Decorate a callable with this requirement.
        """
        if isinstance(f, ServiceLevel):
            return self._require(f, "**UNKNOWN**")
        return CallableRequirement(self._require, f)


@final
class CallableRequirement[RequirementT, **P, ReturnT, MagicT = Any]:
    """
    A requirement that can be called or used as a descriptor.
    """

    def __init__(
        self,
        require: Callable[[ServiceLevel, str], Awaitable[RequirementT]],
        f: Callable[Concatenate[RequirementT, P], Awaitable[ReturnT] | ReturnT]
        | Callable[Concatenate[MagicT, RequirementT, P], Awaitable[ReturnT] | ReturnT],
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
        self, requirement: RequirementT, *args: P.args, **kwargs: P.kwargs
    ) -> ReturnT:
        pass

    @overload
    async def __call__(
        self,
        magic: MagicT,
        requirement: RequirementT,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> ReturnT:
        pass

    async def __call__(self, *args, **kwargs) -> ReturnT:
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
