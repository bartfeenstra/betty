"""
Service plugin management.
"""

from __future__ import annotations

from abc import abstractmethod
from asyncio import gather
from collections.abc import Callable, MutableSequence
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING, Any, Final, Protocol, Self, final, overload, override

from betty.classtools import Singleton
from betty.functools import LazyReCallable
from betty.life_cycle.manage import ManagedLifeCycle
from betty.plugin import PluginDefinition
from betty.plugin.resolve import (
    ResolvablePluginDefinition,
    resolve_plugin_definition,
    resolve_plugin_id,
)
from betty.requirements.plugin_service import PluginServiceRequirement
from betty.service import HasServices, Service, ServiceManager

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from betty.machine_name import MachineName
    from betty.requirement import Requirement
    from betty.service_level import ServiceLevel


type SupportedPlugins = Iterable[ResolvablePluginDefinition]


class _PluginServiceRequirementPlugins[PluginDefinitionT: PluginDefinition](Protocol):
    def __call__(
        self, *plugins: ResolvablePluginDefinition[PluginDefinitionT]
    ) -> PluginServiceRequirement:
        raise NotImplementedError


@final
class _PluginServiceRequirementGetter(Singleton):
    @overload
    def __get__(self, instance: None, owner: type[PluginServiceManager]) -> Self:
        pass

    @overload
    def __get__(
        self,
        instance: PluginServiceManager[HasPluginServices, PluginDefinition, Any, Any],
        owner: type[PluginServiceManager] | None = None,
    ) -> _PluginServiceRequirementPlugins:
        pass

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(PluginServiceRequirement, instance)


class PluginServiceManager[
    OwnerT: HasPluginServices,
    PluginDefinitionT: PluginDefinition,
    GetServiceT,
    InitT,
](
    ServiceManager[
        OwnerT,
        GetServiceT,
        GetServiceT,
        Callable[[], GetServiceT],
        GetServiceT,
    ]
):
    """
    A plugin service manager.
    """

    require: Final[_PluginServiceRequirementGetter] = _PluginServiceRequirementGetter()

    def __init__(self, plugin_type: type[PluginDefinitionT], /, *, auto: bool = True):
        super().__init__(self.new_service)
        self.plugin_type: Final[type[PluginDefinitionT]] = plugin_type
        """
        The type of service plugin.
        """
        self.auto: Final[bool] = auto
        """
        Whether to automatically initialize plugins that declare themselves able to be enabled automatically.
        """

    @override
    def pre_init_owner(self, owner: OwnerT, /) -> None:
        super().pre_init_owner(owner)
        setattr(owner, f"_plugin_service_init_plugins_{self.prop.name}", [])

    @final
    @override
    def _new_service_getter(self, owner: OwnerT, /) -> Callable[[], GetServiceT]:
        def plugin_service_manager_getter() -> GetServiceT:
            factory = self._get_service_or_factory(owner)
            if isinstance(factory, Service):
                return factory.service
            return factory(owner)

        return LazyReCallable(plugin_service_manager_getter)

    @final
    @override
    def _get_service(self, service: Callable[[], GetServiceT], /) -> GetServiceT:
        return service()

    @final
    def __get_init_plugins(
        self, owner: OwnerT, /
    ) -> MutableSequence[InitT | ResolvablePluginDefinition[PluginDefinitionT]]:
        return getattr(owner, f"_plugin_service_init_plugins_{self.prop.name}")

    @final
    def get_init_plugins(
        self, owner: OwnerT, /
    ) -> Iterable[InitT | ResolvablePluginDefinition[PluginDefinitionT]]:
        """
        Get the initial plugins for the given service provider.
        """
        return self.__get_init_plugins(owner)

    @final
    def add_init_plugins(
        self,
        owner: OwnerT,
        /,
        *plugins: InitT | ResolvablePluginDefinition[PluginDefinitionT],
    ) -> None:
        """
        Add one or more plugins to initialize.
        """
        owner.assert_not_initialized()
        self.__get_init_plugins(owner).extend(plugins)

    @final
    async def init_plugins(
        self,
        owner: OwnerT,
        /,
        *plugins: InitT | ResolvablePluginDefinition[PluginDefinitionT],
    ) -> None:
        """
        Initialize the plugins.
        """
        setattr(
            owner,
            f"_plugin_service_plugins_{self.prop.name}",
            tuple(await self.prepare_plugins(owner, *plugins)),
        )

    async def prepare_plugins(
        self,
        owner: OwnerT,
        /,
        *plugins: InitT | ResolvablePluginDefinition[PluginDefinitionT],
    ) -> Iterable[InitT | ResolvablePluginDefinition[PluginDefinitionT]]:
        """
        Prepare the init plugins before the service is initialized.

        Perform actions such as validation or ordering here.
        """
        # Deduplicate init plugins, where later ones override earlier ones.
        return {
            self.resolve_init_plugin_id(plugin): plugin for plugin in plugins
        }.values()

    @final
    def get_plugins(
        self, owner: OwnerT, /
    ) -> Sequence[InitT | ResolvablePluginDefinition[PluginDefinitionT]]:
        """
        Get the initialized plugins.
        """
        owner.assert_initialized()
        return getattr(owner, f"_plugin_service_plugins_{self.prop.name}")

    @abstractmethod
    def new_service(self, owner: OwnerT, /) -> GetServiceT:
        """
        Create the new service value for the given service provider.
        """

    def resolve_init_plugin_id(
        self, plugin: InitT | ResolvablePluginDefinition[PluginDefinitionT], /
    ) -> MachineName:
        """
        Resolve a service plugin definition to its plugin ID.
        """
        return resolve_plugin_id(plugin)


@final
class PluginServiceInitializer(ManagedLifeCycle):
    """
    The plugin service initializer.
    """

    def __init__(
        self,
        services: ServiceLevel,
        owner: HasPluginServices,
        supported_plugins: SupportedPlugins = (),
        /,
    ):
        super().__init__()
        self._services = services
        self._owner = owner
        self._supported_plugins: Sequence[PluginDefinition] = tuple(
            map(
                resolve_plugin_definition,
                supported_plugins,  # ty:ignore[invalid-argument-type]
            )
        )  # ty:ignore[invalid-assignment]
        self._plugin_services: Sequence[
            PluginServiceManager[HasPluginServices, PluginDefinition, Any, Any]
        ] = tuple(
            prop for prop in owner.props() if isinstance(prop, PluginServiceManager)
        )  # ty:ignore[invalid-assignment]
        self.life_cycle.on_bootstrap(self._initialize_plugin_services)

    async def _initialize_plugin_services(self) -> None:
        init_plugins = chain(
            *await gather(*[
                *(
                    self._collect_init_plugin(service, init_plugin)
                    for service in self._plugin_services
                    for init_plugin in service.get_init_plugins(self._owner)
                ),
                self._collect_auto_plugins(),
                *(
                    self._collect_plugin_requirements(
                        type(supported_plugin), supported_plugin.id
                    )
                    for supported_plugin in self._supported_plugins
                ),
            ])
        )
        service_init_plugins = {service: [] for service in self._plugin_services}
        for service, plugin in init_plugins:
            service_init_plugins[service].append(plugin)
        await gather(*[
            service.init_plugins(self._owner, *plugins)
            for service, plugins in service_init_plugins.items()
        ])

    async def _collect_init_plugin[InitT](
        self,
        service: PluginServiceManager[HasPluginServices, PluginDefinition, Any, InitT],
        init_plugin: InitT,
    ) -> Iterable[tuple[PluginServiceManager, Any]]:
        plugin = await self._services.plugins[service.plugin_type][
            service.resolve_init_plugin_id(init_plugin)
        ]
        return (
            (service, init_plugin),
            *chain(*await gather(*map(self._collect_requirement, plugin.requires))),
        )

    async def _collect_auto_plugins(
        self,
    ) -> Iterable[tuple[PluginServiceManager, PluginDefinition]]:
        return chain(*[
            (
                (service, plugin),
                *await self._collect_plugin_requirements(type(plugin), plugin.id),
            )
            for service in self._plugin_services
            if service.auto
            async for plugin in self._services.plugins[service.plugin_type]
            if plugin.auto
        ])

    async def _collect_plugin_requirements(
        self, plugin_type: type[PluginDefinition], plugin_id: MachineName
    ) -> Iterable[tuple[PluginServiceManager, PluginDefinition]]:
        plugin = await self._services.plugins[plugin_type][plugin_id]
        return chain(*await gather(*map(self._collect_requirement, plugin.requires)))

    async def _collect_requirement(
        self, requirement: Requirement
    ) -> Iterable[tuple[PluginServiceManager, PluginDefinition]]:
        if isinstance(requirement, PluginServiceRequirement):
            return (
                *[(requirement.service, plugin) for plugin in requirement.plugins],
                *chain(
                    *await gather(*[
                        self._collect_plugin_requirements(
                            requirement.service.plugin_type,  # ty:ignore[invalid-argument-type]
                            plugin.id,  # ty:ignore[unresolved-attribute]
                        )
                        for plugin in requirement.plugins
                    ])
                ),
            )  # ty:ignore[invalid-return-type]
        return ()


class HasPluginServices(HasServices):
    """
    A plugin service provider.
    """

    def __init__(
        self,
        *args: Any,
        services: ServiceLevel,
        supported_plugins: SupportedPlugins = (),
        **kwargs: Any,
    ):
        super().__init__(*args, services=services, **kwargs)
        initializer = PluginServiceInitializer(services, self, supported_plugins)
        self.life_cycle.on((initializer.bootstrap, initializer.shutdown))
