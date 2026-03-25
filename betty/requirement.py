"""
Requirements checking.
"""

from __future__ import annotations

from contextlib import suppress
from functools import partial, update_wrapper
from typing import TYPE_CHECKING, Any, Concatenate, final, overload

from betty.asyncio import resolve_await
from betty.exception import HumanFacingException
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.service.level import ChainedServiceLevel, ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from betty.machine_name import MachineName
    from betty.plugin import Plugin, PluginDefinition
    from betty.plugin.factory import PluginManufacturer
    from betty.service.plugin import ServicePluginDefinition


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
        update_wrapper(self, f)
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


class ServicePluginRequirement[ServicePluginDefinitionT: ServicePluginDefinition]:
    """
    Check that a service plugin is available.
    """

    def __init__(
        self, plugin_type: type[ServicePluginDefinitionT], plugin_id: MachineName, /
    ):
        self._plugin_type = plugin_type
        self._plugin_id = plugin_id

    @property
    def plugin_type(self) -> type[ServicePluginDefinition]:
        """
        The plugin type.
        """
        return self._plugin_type

    @property
    def plugin_id(self) -> MachineName:
        """
        The plugin ID.
        """
        return self._plugin_id

    @final
    async def __call__(
        self, services: ServiceLevel, /
    ) -> Plugin[ServicePluginDefinitionT]:
        """
        Check the requirement.
        """
        from betty.service.plugin import ServicePluginProvider

        if isinstance(services, ServicePluginProvider):
            service_plugins = await services.service_plugins
            with suppress(KeyError):
                return service_plugins[self.plugin_type][self._plugin_id]
        if isinstance(services, ChainedServiceLevel):
            return await self(services.upstream)
        raise UnmetRequirement(
            _("The {plugin_id} {plugin_type} is required.").format(
                plugin_id=self._plugin_id,
                plugin_type=self.plugin_type.type().label,
            )
        )


@final
class ManufacturableServicePluginRequirement[
    PluginDefinitionT: ServicePluginDefinition
](ServicePluginRequirement):
    """
    Check that a service plugin is available.
    """

    def __init__(
        self,
        manufacturer: PluginManufacturer[PluginDefinitionT, Plugin[PluginDefinitionT]],
        /,
    ):
        super().__init__()
        self._manufacturer = manufacturer

    @property
    def manufacturer(
        self,
    ) -> PluginManufacturer[PluginDefinitionT, Plugin[PluginDefinitionT]]:
        """
        The plugin manufacturer.
        """
        return self._manufacturer


@final
class PluginRequirementsRequirement:
    """
    Check that a plugin's requirements are met.
    """

    def __init__(self, plugin_type: type[PluginDefinition], plugin_id: MachineName, /):
        self._plugin_type = plugin_type
        self._plugin_id = plugin_id

    @property
    def plugin_type(self) -> type[PluginDefinition]:
        """
        The plugin type.
        """
        return self._plugin_type

    @property
    def plugin_id(self) -> MachineName:
        """
        The plugin ID.
        """
        return self._plugin_id

    async def __call__(self, services: ServiceLevel, /) -> None:
        """
        Check the requirement.
        """
        for requirement in (
            await services.plugins[self._plugin_type][self._plugin_id]
        ).requires:
            await requirement(services)


if TYPE_CHECKING:
    type ResolvableRequirement[ResultT] = (
        Requirement[ResultT]
        | type[ServiceLevel]
        | type[Plugin[ServicePluginDefinition]]
    )
else:
    type ResolvableRequirement = Any


def resolve_requirement(requirement: ResolvableRequirement[Any], /) -> Requirement[Any]:
    """
    Resolve a requirement on a service level or plugin.
    """
    if isinstance(requirement, type):
        if issubclass(requirement, ServiceLevel):
            return ServiceLevelRequirement(requirement)
        return ServicePluginRequirement(requirement)
    return requirement


if TYPE_CHECKING:
    type Requires = Iterable[ResolvableRequirement]
else:
    type Requires = Any


class HasRequirements:
    """
    An object that exposes requirements.
    """

    def __init__(self, *args: Any, requires: Requires | None = None, **kwargs: Any):

        super().__init__(*args, **kwargs)
        self.__requires = (
            () if requires is None else tuple(map(resolve_requirement, requires))
        )

    @property
    def requires(self) -> Iterable[Requirement]:
        """
        The requirements.
        """
        return self.__requires
