"""
Requirements checking.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import gather
from functools import partial
from typing import TYPE_CHECKING, Any, Concatenate, Self, final, overload, override

from betty.asyncio import resolve_await
from betty.exception import HumanFacingException
from betty.functools import CallableDecorator, DecoratedCallable, DecoratedCallableType

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from betty.service_level import ServiceLevel


type Requirement[CheckT] = Callable[[ServiceLevel], Awaitable[CheckT] | CheckT]


class UnmetRequirement(HumanFacingException):
    """
    Raised when a requirement is not met.
    """


type Requires[CheckT] = Iterable[Requirement[CheckT]]


class RequirableDecorator[CheckT](CallableDecorator, ABC):
    """
    A base class for requirements that can also be used as decorators.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(callable_decorator=partial(_RequirableDecorator, self._check))

    @overload
    async def __call__(self, services: ServiceLevel, /) -> CheckT:
        pass

    @overload
    def __call__(self) -> Self:
        pass

    @overload
    def __call__[**P, ReturnT](
        self,
        decorated: DecoratedCallableType[
            Concatenate[CheckT, P],
            Awaitable[ReturnT] | ReturnT,
        ],
    ) -> DecoratedCallable[Concatenate[ServiceLevel, P], Awaitable[ReturnT]]:
        pass

    @override
    def __call__(self, services_or_decorated=None, *args, **kwargs):
        from betty.service_level import ServiceLevel

        if isinstance(services_or_decorated, ServiceLevel):
            return self._check(services_or_decorated)
        return super().__call__(services_or_decorated)

    @abstractmethod
    async def _check(self, services: ServiceLevel, /) -> CheckT:
        """
        Check the requirement.
        """


@final
class _RequirableDecorator[CheckT, **P, ReturnT]:
    __slots__ = "_check", "_decorated"

    def __init__(
        self,
        check: Callable[[ServiceLevel], Awaitable[CheckT]],
        decorated: Callable[
            Concatenate[CheckT, P],
            Awaitable[ReturnT] | ReturnT,
        ],
        /,
    ):
        self._check = check
        self._decorated = decorated

    async def __call__(
        self, services: ServiceLevel, *args: P.args, **kwargs: P.kwargs
    ) -> ReturnT:
        return await resolve_await(
            self._decorated(await self._check(services), *args, **kwargs)
        )


async def check(services: ServiceLevel, *requirements: Requirement) -> bool:
    """
    Check if one or more requirements are met.
    """
    try:
        await gather(*[
            resolve_await(requirement(services)) for requirement in requirements
        ])
    except UnmetRequirement:
        return False
    return True
