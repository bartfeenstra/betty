"""
Service plugin management.
"""

from __future__ import annotations

from abc import abstractmethod
from asyncio import gather
from collections.abc import Callable, MutableSequence
from functools import partial
from inspect import getmembers
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
from betty.service import (
    Service,
    ServiceAlreadyInitialized,
    ServiceManager,
    ServiceNotYetInitialized,
    ServiceProvider,
)
from betty.service.plugin.requirement import PluginServiceRequirement

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from betty.machine_name import MachineName
    from betty.requirement import Requirement
    from betty.service_level import ServiceLevel
    from betty.typing import Intersection as Intersection


type SupportedPlugins = Iterable[ResolvablePluginDefinition]


class _PluginServiceRequirementPlugins[
    UpstreamPluginDefinitionT: PluginDefinition,
    UpstreamGetServiceT,
](Protocol):
    @overload
    def __call__[DownstreamPluginDefinitionT: PluginDefinition, DownstreamGetServiceT](
        self,
        downstream: PluginServiceManager[
            PluginServiceProvider,
            DownstreamPluginDefinitionT,
            DownstreamGetServiceT,
            Any,
        ],
        *plugins: ResolvablePluginDefinition[DownstreamPluginDefinitionT],
    ) -> PluginServiceRequirement[DownstreamPluginDefinitionT, DownstreamGetServiceT]:
        pass  # pragma: nocover

    @overload
    def __call__(
        self, *plugins: ResolvablePluginDefinition[UpstreamPluginDefinitionT]
    ) -> PluginServiceRequirement[UpstreamPluginDefinitionT, UpstreamGetServiceT]:
        pass  # pragma: nocover


@final
class _PluginServiceRequirementGetter(Singleton):
    @overload
    def __get__(self, instance: None, owner: type[PluginServiceManager]) -> Self:
        pass

    @overload
    def __get__[UpstreamPluginDefinitionT: PluginDefinition, UpstreamGetServiceT](
        self,
        instance: PluginServiceManager[
            PluginServiceProvider, UpstreamPluginDefinitionT, UpstreamGetServiceT, Any
        ],
        owner: type[PluginServiceManager] | None = None,
    ) -> _PluginServiceRequirementPlugins[
        UpstreamPluginDefinitionT, UpstreamGetServiceT
    ]:
        pass

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(PluginServiceRequirement, instance)


class PluginServiceManager[
    ServiceProviderT: PluginServiceProvider,
    PluginDefinitionT: PluginDefinition,
    GetServiceT,
    InitT,
](
    ServiceManager[
        ServiceProviderT,
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
        self.__plugin_type = plugin_type
        self.__auto = auto

    @final
    @property
    def plugin_type(self) -> type[PluginDefinitionT]:
        """
        The type of service plugin.
        """
        return self.__plugin_type

    @final
    @property
    def auto(self) -> bool:
        """
        Whether to automatically initialize plugins that declare themselves able to be enabled automatically.
        """
        return self.__auto

    @override
    def init(self, service_provider: ServiceProviderT, /) -> None:
        super().init(service_provider)
        setattr(service_provider, f"_plugin_service_init_plugins_{self.name}", [])

    @final
    @override
    def _new_service_getter(
        self, service_provider: ServiceProviderT, /
    ) -> Callable[[], GetServiceT]:
        def plugin_service_manager_getter() -> GetServiceT:
            factory = self._get_service_or_factory(service_provider)
            if isinstance(factory, Service):
                return factory.service
            return factory(service_provider)

        return LazyReCallable(plugin_service_manager_getter)

    @final
    @override
    def _get_service(self, service: Callable[[], GetServiceT], /) -> GetServiceT:
        return service()

    @final
    def __get_init_plugins(
        self, service_provider: ServiceProviderT, /
    ) -> MutableSequence[InitT | ResolvablePluginDefinition[PluginDefinitionT]]:
        return getattr(service_provider, f"_plugin_service_init_plugins_{self.name}")

    @final
    def get_init_plugins(
        self, service_provider: ServiceProviderT, /
    ) -> Iterable[InitT | ResolvablePluginDefinition[PluginDefinitionT]]:
        """
        Get the initial plugins for the given service provider.
        """
        return self.__get_init_plugins(service_provider)

    @final
    def add_init_plugins(
        self,
        service_provider: ServiceProviderT,
        /,
        *plugins: InitT | ResolvablePluginDefinition[PluginDefinitionT],
    ) -> None:
        """
        Add one or more plugins to initialize.
        """
        self.assert_plugins_not_initialized(service_provider)
        self.__get_init_plugins(service_provider).extend(plugins)

    @final
    async def init_plugins(
        self,
        service_provider: ServiceProviderT,
        /,
        *plugins: InitT | ResolvablePluginDefinition[PluginDefinitionT],
    ) -> None:
        """
        Initialize the plugins.
        """
        self.assert_plugins_not_initialized(service_provider)
        setattr(
            service_provider,
            f"_plugin_service_plugins_{self.name}",
            tuple(await self.prepare_plugins(service_provider, *plugins)),
        )

    async def prepare_plugins(
        self,
        service_provider: ServiceProviderT,
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
        self, service_provider: ServiceProviderT, /
    ) -> Sequence[InitT | ResolvablePluginDefinition[PluginDefinitionT]]:
        """
        Get the initialized plugins.
        """
        self.assert_plugins_initialized(service_provider)
        return getattr(service_provider, f"_plugin_service_plugins_{self.name}")

    @final
    def assert_plugins_not_initialized(
        self, service_provider: ServiceProviderT, /
    ) -> None:
        """
        Assert that the plugins have not yet been initialized for the given service provider.

        :raise ServiceAlreadyInitialized:
        """
        if hasattr(service_provider, f"_plugin_service_plugins_{self.name}"):
            raise ServiceAlreadyInitialized(
                f"Service {self.id}'s plugins were initialized already."
            )

    @final
    def assert_plugins_initialized(self, service_provider: ServiceProviderT, /) -> None:
        """
        Assert that the plugins have been initialized already for the given service provider.

        :raise ServiceNotYetInitialized:
        """
        if not hasattr(service_provider, f"_plugin_service_plugins_{self.name}"):
            raise ServiceNotYetInitialized(
                f"Service {self.id}'s plugins were not yet initialized."
            )

    @abstractmethod
    def new_service(self, service_provider: ServiceProviderT, /) -> GetServiceT:
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
        service_provider: Any,
        supported_plugins: SupportedPlugins = (),
        /,
    ):
        super().__init__()
        self._services = services
        self._service_provider = service_provider
        self._supported_plugins = tuple(
            map(resolve_plugin_definition, supported_plugins)
        )
        self._plugin_services = tuple(
            member[1]
            for member in getmembers(type(service_provider))
            if isinstance(member[1], PluginServiceManager)
        )
        self.life_cycle.on_bootstrap(self._initialize_plugin_services)

    async def _initialize_plugin_services(self) -> None:
        init_plugins = chain(
            *await gather(*[
                *(
                    self._collect_init_plugin(service, init_plugin)
                    for service in self._plugin_services
                    for init_plugin in service.get_init_plugins(self._service_provider)
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
            service.init_plugins(self._service_provider, *plugins)
            for service, plugins in service_init_plugins.items()
        ])

    async def _collect_init_plugin[InitT](
        self,
        service: PluginServiceManager[
            PluginServiceProvider, PluginDefinition, Any, InitT
        ],
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
                            requirement.service.plugin_type, plugin.id
                        )
                        for plugin in requirement.plugins
                    ])
                ),
            )
        return ()


class PluginServiceProvider[ServiceLevelT: ServiceLevel](
    ManagedLifeCycle, ServiceProvider[ServiceLevelT]
):
    """
    A plugin service provider.
    """

    def __init__(
        self,
        *args: Any,
        services: ServiceLevelT,
        supported_plugins: SupportedPlugins = (),
        **kwargs: Any,
    ):
        super().__init__(*args, services=services, **kwargs)
        initializer = PluginServiceInitializer(self.services, self, supported_plugins)
        self.life_cycle.on((initializer.bootstrap, initializer.shutdown))
