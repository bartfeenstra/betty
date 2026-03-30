from collections.abc import Sequence
from typing import override

import pytest

from betty.app import App
from betty.machine_name import MachineName
from betty.plugin.resolve import ResolvablePluginDefinition
from betty.service.level import ServiceLevel
from betty.service.plugin.service import (
    PluginServiceInitializer,
    PluginServiceManager,
    PluginServiceProvider,
)
from betty.service.plugin.service.definition.collection.keyed import (
    PluginDefinitionsService,
)
from betty.service.provider import (
    Service,
    ServiceAlreadyInitialized,
    ServiceNotYetInitialized,
)
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginManufacturer,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
    DummyPluginWithLifeCycle,
)


class TestPluginServiceInitializer:
    async def test_bootstrap__without_services(self) -> None:
        async with PluginServiceInitializer(ServiceLevel(), object()):
            pass

    async def test_bootstrap__without_plugins(self, isolated_app: App) -> None:
        class ServiceProvider(PluginServiceProvider):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

        service_provider = ServiceProvider(
            services=ServiceLevel(plugins={DummyPluginDefinition: []})
        )
        async with service_provider:
            assert not service_provider.plugins

    async def test_bootstrap__with_isolated(self, isolated_app: App) -> None:
        class ServiceProvider(PluginServiceProvider):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

        plugin = DummyPluginDefinition("plugin")
        service_provider = ServiceProvider(
            services=ServiceLevel(plugins={DummyPluginDefinition: [plugin]})
        )
        ServiceProvider.plugins.add_init_plugins(service_provider, plugin)
        async with service_provider:
            assert plugin in service_provider.plugins

    async def test_bootstrap__without_auto_service_without_auto_plugin(
        self, isolated_app: App
    ) -> None:
        class ServiceProvider(PluginServiceProvider):
            plugins = PluginDefinitionsService(DummyPluginDefinition, auto=False)

        service_provider = ServiceProvider(
            services=ServiceLevel(
                plugins={DummyPluginDefinition: [DummyPluginDefinition("plugin")]}
            )
        )
        async with service_provider:
            assert not service_provider.plugins

    async def test_bootstrap__without_auto_service_with_auto_plugin(
        self, isolated_app: App
    ) -> None:
        class ServiceProvider(PluginServiceProvider):
            plugins = PluginDefinitionsService(DummyPluginDefinition, auto=False)

        service_provider = ServiceProvider(
            services=ServiceLevel(
                plugins={
                    DummyPluginDefinition: [DummyPluginDefinition("plugin", auto=True)]
                }
            )
        )
        async with service_provider:
            assert not service_provider.plugins

    async def test_bootstrap__with_auto_service_without_auto_plugin(
        self, isolated_app: App
    ) -> None:
        class ServiceProvider(PluginServiceProvider):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

        service_provider = ServiceProvider(
            services=ServiceLevel(
                plugins={DummyPluginDefinition: [DummyPluginDefinition("plugin")]}
            )
        )
        async with service_provider:
            assert not service_provider.plugins

    async def test_bootstrap__with_auto_service_with_auto_plugin(
        self, isolated_app: App
    ) -> None:
        class ServiceProvider(PluginServiceProvider):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

        plugin = DummyPluginDefinition("plugin", auto=True)
        service_provider = ServiceProvider(
            services=ServiceLevel(plugins={DummyPluginDefinition: [plugin]})
        )
        async with service_provider:
            assert plugin in service_provider.plugins

    async def test_bootstrap__with_irrelevant_requirement(
        self, isolated_app: App
    ) -> None:
        class ServiceProvider(PluginServiceProvider):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

        plugin = DummyPluginDefinition("dependent", requires={lambda _: None})
        service_provider = ServiceProvider(
            services=ServiceLevel(plugins={DummyPluginDefinition: [plugin]})
        )
        ServiceProvider.plugins.add_init_plugins(service_provider, plugin)
        async with service_provider:
            assert plugin in service_provider.plugins

    async def test_bootstrap__with_plugin_service_requirement(
        self, isolated_app: App
    ) -> None:
        class ServiceProvider(PluginServiceProvider):
            dependencies = PluginDefinitionsService(DummyPluginDefinition)
            dependents = PluginDefinitionsService(DummyPluginDefinition)

        dependency = DummyPluginDefinition("dependency")
        dependent = DummyPluginDefinition(
            "dependent", requires={ServiceProvider.dependencies.require(dependency)}
        )
        service_provider = ServiceProvider(
            services=ServiceLevel(
                plugins={DummyPluginDefinition: [dependent, dependency]}
            )
        )
        ServiceProvider.dependents.add_init_plugins(service_provider, dependent)
        async with service_provider:
            assert dependent in service_provider.dependents
            assert dependency in service_provider.dependencies

    async def test_bootstrap__with_supported_plugin_plugin_service_requirement(
        self, isolated_app: App
    ) -> None:
        class ServiceProvider(PluginServiceProvider):
            dependencies = PluginDefinitionsService(DummyPluginDefinition)
            dependents = PluginDefinitionsService(DummyPluginDefinition)

        dependency = DummyPluginDefinition("dependency")
        dependent = DummyPluginDefinition(
            "dependent", requires={ServiceProvider.dependencies.require(dependency)}
        )
        service_provider = ServiceProvider(
            services=ServiceLevel(
                plugins={DummyPluginDefinition: [dependent, dependency]}
            ),
            supported_plugins={dependent},
        )
        async with service_provider:
            assert dependent not in service_provider.dependents
            assert dependency in service_provider.dependencies


class PluginServiceManagerTestBase:
    _SERVICES = ServiceLevel(
        plugins={
            DummyPluginDefinition: [
                DummyPluginOne,
                DummyPluginTwo,
                DummyPluginThree,
                DummyPluginWithLifeCycle,
            ]
        }
    )


class TestPluginServiceProvider:
    async def test(self) -> None:
        async with PluginServiceProvider(services=ServiceLevel(plugins={})):
            pass


class _PluginServiceManagerTestSut(
    PluginServiceManager[
        PluginServiceProvider,
        DummyPluginDefinition,
        Sequence[MachineName],
        ResolvablePluginDefinition[DummyPluginDefinition] | DummyPluginManufacturer,
    ]
):
    def __init__(self, *, auto: bool = True):
        super().__init__(DummyPluginDefinition, auto=auto)

    @override
    def new_service(
        self, service_provider: PluginServiceProvider, /
    ) -> Sequence[MachineName]:
        raise NotImplementedError


class _PluginServiceManagerTestServiceProvider(PluginServiceProvider):
    my_first_service = _PluginServiceManagerTestSut()


class TestPluginServiceManager:
    def test___set_name__(self) -> None:
        assert (
            _PluginServiceManagerTestServiceProvider.my_first_service.name
            == "my_first_service"
        )

    def test_add_init_plugins(self) -> None:
        service_provider = _PluginServiceManagerTestServiceProvider(
            services=ServiceLevel()
        )
        _PluginServiceManagerTestServiceProvider.my_first_service.add_init_plugins(
            service_provider, DummyPluginOne.plugin(), DummyPluginTwo.plugin()
        )
        init_plugins = (
            _PluginServiceManagerTestServiceProvider.my_first_service.get_init_plugins(
                service_provider
            )
        )
        assert tuple(init_plugins) == (DummyPluginOne.plugin(), DummyPluginTwo.plugin())

    async def test_assert_plugins_initialized(self) -> None:
        service_provider = _PluginServiceManagerTestServiceProvider(
            services=ServiceLevel()
        )
        with pytest.raises(ServiceNotYetInitialized):
            _PluginServiceManagerTestServiceProvider.my_first_service.assert_plugins_initialized(
                service_provider
            )
        await _PluginServiceManagerTestServiceProvider.my_first_service.init_plugins(
            service_provider
        )
        _PluginServiceManagerTestServiceProvider.my_first_service.assert_plugins_initialized(
            service_provider
        )

    async def test_assert_plugins_not_initialized(self) -> None:
        service_provider = _PluginServiceManagerTestServiceProvider(
            services=ServiceLevel()
        )
        _PluginServiceManagerTestServiceProvider.my_first_service.assert_plugins_not_initialized(
            service_provider
        )
        await _PluginServiceManagerTestServiceProvider.my_first_service.init_plugins(
            service_provider
        )
        with pytest.raises(ServiceAlreadyInitialized):
            _PluginServiceManagerTestServiceProvider.my_first_service.assert_plugins_not_initialized(
                service_provider
            )

    def test_auto__without_auto(self) -> None:
        sut = _PluginServiceManagerTestSut(auto=False)
        assert not sut.auto

    def test_auto__with_auto(self) -> None:
        sut = _PluginServiceManagerTestSut(auto=True)
        assert sut.auto

    def test_get_init_plugins__without_plugins(self) -> None:
        assert not _PluginServiceManagerTestServiceProvider.my_first_service.get_init_plugins(
            _PluginServiceManagerTestServiceProvider(services=ServiceLevel())
        )

    async def test_get_init_plugins__with_plugins(self) -> None:
        service_provider = _PluginServiceManagerTestServiceProvider(
            services=ServiceLevel()
        )
        _PluginServiceManagerTestServiceProvider.my_first_service.add_init_plugins(
            service_provider, DummyPluginOne
        )
        assert (
            _PluginServiceManagerTestServiceProvider.my_first_service.get_init_plugins(
                service_provider
            )
            == [DummyPluginOne]
        )

    async def test_get_plugins__with_plugins(self) -> None:
        service_provider = _PluginServiceManagerTestServiceProvider(
            services=ServiceLevel()
        )
        await _PluginServiceManagerTestServiceProvider.my_first_service.init_plugins(
            service_provider, DummyPluginOne
        )
        assert list(
            _PluginServiceManagerTestServiceProvider.my_first_service.get_plugins(
                service_provider
            )
        ) == [DummyPluginOne]

    async def test_get_plugins__without_plugins(self) -> None:
        service_provider = _PluginServiceManagerTestServiceProvider(
            services=ServiceLevel()
        )
        await _PluginServiceManagerTestServiceProvider.my_first_service.init_plugins(
            service_provider
        )
        assert (
            not _PluginServiceManagerTestServiceProvider.my_first_service.get_plugins(
                service_provider
            )
        )

    def test_init(self) -> None:
        service_provider = _PluginServiceManagerTestServiceProvider(
            services=ServiceLevel()
        )
        assert not _PluginServiceManagerTestServiceProvider.my_first_service.get_init_plugins(
            service_provider
        )

    async def test_init_plugins__without_plugins(self) -> None:
        service_provider = _PluginServiceManagerTestServiceProvider(
            services=ServiceLevel()
        )
        await _PluginServiceManagerTestServiceProvider.my_first_service.init_plugins(
            service_provider
        )

    async def test_init_plugins__with_plugins_already_initialized(self) -> None:
        service_provider = _PluginServiceManagerTestServiceProvider(
            services=ServiceLevel()
        )
        await _PluginServiceManagerTestServiceProvider.my_first_service.init_plugins(
            service_provider
        )
        with pytest.raises(ServiceAlreadyInitialized):
            await (
                _PluginServiceManagerTestServiceProvider.my_first_service.init_plugins(
                    service_provider
                )
            )

    def test_override(self) -> None:
        machine_names = [MachineName("foo"), MachineName("bar")]

        class _ServiceProvider(_PluginServiceManagerTestServiceProvider):
            def __init__(self):
                type(self).my_first_service.override(self, Service(machine_names))
                super().__init__(services=ServiceLevel())

        service_provider = _ServiceProvider()
        assert service_provider.my_first_service == machine_names

    def test_plugin_type(self) -> None:
        assert _PluginServiceManagerTestSut().plugin_type is DummyPluginDefinition

    async def test_prepare_plugins__without_plugins(self) -> None:
        assert (
            list(
                await _PluginServiceManagerTestSut().prepare_plugins(
                    _PluginServiceManagerTestServiceProvider(services=ServiceLevel())
                )
            )
            == []
        )

    async def test_prepare_plugins__deduplicates(self) -> None:
        assert list(
            await _PluginServiceManagerTestSut().prepare_plugins(
                _PluginServiceManagerTestServiceProvider(services=ServiceLevel()),
                DummyPluginOne,
                DummyPluginOne.plugin(),
                DummyPluginTwo.plugin(),
                DummyPluginOne,
            )
        ) == [DummyPluginOne, DummyPluginTwo.plugin()]

    def test_resolve_init_plugin_id__with_plugin_class(self) -> None:
        assert (
            _PluginServiceManagerTestSut().resolve_init_plugin_id(DummyPluginOne)
            == DummyPluginOne.plugin().id
        )

    def test_resolve_init_plugin_id__with_plugin_definition(self) -> None:
        assert (
            _PluginServiceManagerTestSut().resolve_init_plugin_id(
                DummyPluginOne.plugin()
            )
            == DummyPluginOne.plugin().id
        )
