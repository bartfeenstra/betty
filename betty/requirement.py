"""
Requirements checking.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import partial
from typing import TYPE_CHECKING, Any, Concatenate, Self, final, overload, override

from betty.asyncio import resolve_await
from betty.exception import HumanFacingException
from betty.functools import CallableDecorator, DecoratedCallable, DecoratedCallableType
from betty.locale.localizable.gettext import _
from betty.service.level import ChainedServiceLevel, ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from betty.plugin.cls import Plugin
    from betty.service.plugin.service import ServicePluginDefinition


type Requirement[CheckT] = Callable[[ServiceLevel], Awaitable[CheckT] | CheckT]


class UnmetRequirement(HumanFacingException):
    """
    Raised when a requirement is not met.
    """


@final
class ServicePluginRequirement[ServicePluginT: Plugin[ServicePluginDefinition]]:
    """
    Check that a service plugin is available.
    """

    def __init__(self, plugin: type[ServicePluginT], /):
        self._plugin = plugin

    @property
    def plugin(self) -> type[ServicePluginT]:
        """
        The required service plugin.
        """
        return self._plugin

    async def __call__(self, services: ServiceLevel, /) -> ServicePluginT:
        """
        Check the requirement.
        """
        from betty.service.plugin.service import ServicePluginProvider

        if isinstance(services, ServicePluginProvider):
            service_plugins = await services.service_plugins
            try:
                service_type_plugins = service_plugins[type(self._plugin.plugin())]
            except KeyError:
                if not isinstance(services, ChainedServiceLevel):
                    raise self._raise() from None
            else:
                try:
                    return service_type_plugins[self._plugin]
                except KeyError:
                    raise self._raise() from None
        if isinstance(services, ChainedServiceLevel):
            return await self(services.upstream)
        raise self._raise()

    def _raise(self) -> UnmetRequirement:
        return UnmetRequirement(
            _("The {plugin_id} {plugin_type} is required.").format(
                plugin_id=self._plugin.plugin().id,
                plugin_type=self._plugin.plugin().type().label,
            )
        )


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
