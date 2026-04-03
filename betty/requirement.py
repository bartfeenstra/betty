"""
Requirements checking.
"""

from __future__ import annotations

from functools import partial, update_wrapper
from typing import TYPE_CHECKING, Any, Concatenate, Never, final, overload

from betty.asyncio import resolve_await
from betty.exception import HumanFacingException
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.service.level import ChainedServiceLevel, ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from betty.plugin.cls import Plugin
    from betty.service.plugin.service import ServicePluginDefinition


type Requirement[ResultT] = Callable[[ServiceLevel], Awaitable[ResultT] | ResultT]


@final
class require[ResultT]:
    """
    Decorate a callable to check a requirement.
    """

    def __init__(self, requirement: ResolvableRequirement[ResultT]):
        self._requirement = resolve_requirement(requirement)

    @overload
    def __call__[**P, ReturnT](
        self,
        f: Callable[Concatenate[ResultT, P], Awaitable[ReturnT] | ReturnT],
    ) -> Callable[Concatenate[ServiceLevel, P], Awaitable[ReturnT]]:
        pass

    @overload
    def __call__[**P, ReturnT, ClsOrSelfT](
        self,
        f: Callable[Concatenate[ClsOrSelfT, ResultT, P], Awaitable[ReturnT] | ReturnT],
    ) -> Callable[Concatenate[ClsOrSelfT, ServiceLevel, P], Awaitable[ReturnT]]:
        pass

    def __call__[**P, ReturnT](
        self, f
    ) -> _CallableRequire[ResultT, P, ReturnT] | Awaitable[ResultT]:
        """
        Decorate the callable.
        """
        return _CallableRequire(self._requirement, f)


@final
class _CallableRequire[ResultT, **P, ReturnT, ClsOrSelfT = Any]:
    def __init__(
        self,
        requirement: Requirement[ResultT],
        f: Callable[Concatenate[ResultT, P], Awaitable[ReturnT] | ReturnT]
        | Callable[Concatenate[ClsOrSelfT, ResultT, P], Awaitable[ReturnT] | ReturnT],
    ):
        self._requirement = requirement
        update_wrapper(
            self,
            f,  # ty:ignore[invalid-argument-type]
        )
        self._f = f

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(self, instance)

    @overload
    async def __call__(
        self, requirement: ResultT, *args: P.args, **kwargs: P.kwargs
    ) -> ReturnT:
        pass

    @overload
    async def __call__(
        self,
        magic: ClsOrSelfT,
        requirement: ResultT,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> ReturnT:
        pass

    async def __call__(self, *args, **kwargs) -> ReturnT:
        index = 0 if isinstance(args[0], ServiceLevel) else 1
        return await resolve_await(
            self._f(
                *args[:index],
                await resolve_await(self._requirement(args[index])),
                *args[index + 1 :],
                **kwargs,
            )
        )


class UnmetRequirement(HumanFacingException):
    """
    Raised when a requirement is not met.
    """


@final
class ServiceLevelRequirement[ServiceLevelT: ServiceLevel]:
    """
    Check that a service level is available.
    """

    def __init__(self, services: type[ServiceLevelT], /):
        self._services = services

    @property
    def services(self) -> type[ServiceLevelT]:
        """
        The required service level.
        """
        return self._services

    def __call__(self, services: ServiceLevel, /) -> ServiceLevelT:
        """
        Check the requirement.
        """
        if isinstance(services, self._services):
            return services
        if isinstance(services, ChainedServiceLevel):
            return self(services.upstream)
        raise UnmetRequirement(
            f"This requires a(n) {fully_qualified_name(self._services)}"
        )


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

    async def __call__(self, services: ServiceLevel, /) -> ServicePluginT:  # noqa: RET503
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
                    self._raise()
            else:
                try:
                    return service_type_plugins[self._plugin]
                except KeyError:
                    self._raise()
        if isinstance(services, ChainedServiceLevel):
            return await self(services.upstream)
        self._raise()

    def _raise(self) -> Never:
        raise UnmetRequirement(
            _("The {plugin_id} {plugin_type} is required.").format(
                plugin_id=self._plugin.plugin().id,
                plugin_type=self._plugin.plugin().type().label,
            )
        )


if TYPE_CHECKING:
    type ResolvableRequirement[ResultT] = (
        Requirement[ResultT]
        | type[ServiceLevel]
        | type[Plugin[ServicePluginDefinition]]
    )
    type Requires = Iterable[ResolvableRequirement]
else:
    type ResolvableRequirement = Any
    type Requires = Any


def resolve_requirement(requirement: ResolvableRequirement[Any], /) -> Requirement[Any]:
    """
    Resolve a requirement on a service level or plugin.
    """
    if isinstance(requirement, type):
        if issubclass(requirement, ServiceLevel):
            return ServiceLevelRequirement(requirement)
        return ServicePluginRequirement(requirement)
    return requirement
