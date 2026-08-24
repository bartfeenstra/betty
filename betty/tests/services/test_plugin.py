from collections.abc import Iterable, Sequence
from typing import ClassVar, override

from betty.app import App
from betty.machine_name import MachineName
from betty.plugin.resolve import ResolvablePluginDefinition
from betty.service import Service
from betty.service_level import HasServiceLevel, ServiceLevel
from betty.services.plugin import (
    HasPluginServices,
    PluginServiceManager,
    ResolvableServiceLevelHasPluginServices,
)
from betty.services.plugin.definition.collection.keyed import (
    PluginDefinitionsService,
)
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginManufacturer,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
    DummyPluginWithLifeCycle,
)


class _HasPluginServices(HasPluginServices, HasServiceLevel):
    pass


class TestHasPluginServices:
    async def test_bootstrap__without_services(self) -> None:
        services = ServiceLevel()
        async with _HasPluginServices(services=services) as sut:
            assert sut.services is services

    async def test_bootstrap__without_plugins(self, isolated_app: App) -> None:
        class _Owner(_HasPluginServices):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

        owner = _Owner(services=ServiceLevel(plugins={DummyPluginDefinition: []}))
        async with owner:
            assert not owner.plugins

    async def test_bootstrap__with_isolated(self, isolated_app: App) -> None:
        plugin = DummyPluginDefinition("plugin")

        class _Owner(_HasPluginServices):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

            def __init__(self):
                super().__init__(
                    services=ServiceLevel(plugins={DummyPluginDefinition: [plugin]})
                )
                type(self).plugins.add_init_plugins(self, plugin)

        async with _Owner() as owner:
            assert plugin in owner.plugins

    async def test_bootstrap__without_auto_service_without_auto_plugin(
        self, isolated_app: App
    ) -> None:
        class _Owner(_HasPluginServices):
            plugins = PluginDefinitionsService(DummyPluginDefinition, auto=False)

        owner = _Owner(
            services=ServiceLevel(
                plugins={DummyPluginDefinition: [DummyPluginDefinition("plugin")]}
            )
        )
        async with owner:
            assert not owner.plugins

    async def test_bootstrap__without_auto_service_with_auto_plugin(
        self, isolated_app: App
    ) -> None:
        class _Owner(_HasPluginServices):
            plugins = PluginDefinitionsService(DummyPluginDefinition, auto=False)

        owner = _Owner(
            services=ServiceLevel(
                plugins={
                    DummyPluginDefinition: [DummyPluginDefinition("plugin", auto=True)]
                }
            )
        )
        async with owner:
            assert not owner.plugins

    async def test_bootstrap__with_auto_service_without_auto_plugin(
        self, isolated_app: App
    ) -> None:
        class _Owner(_HasPluginServices):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

        owner = _Owner(
            services=ServiceLevel(
                plugins={DummyPluginDefinition: [DummyPluginDefinition("plugin")]}
            )
        )
        async with owner:
            assert not owner.plugins

    async def test_bootstrap__with_auto_service_with_auto_plugin(
        self, isolated_app: App
    ) -> None:
        class _Owner(_HasPluginServices):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

        plugin = DummyPluginDefinition("plugin", auto=True)
        owner = _Owner(services=ServiceLevel(plugins={DummyPluginDefinition: [plugin]}))
        async with owner:
            assert plugin in owner.plugins

    async def test_bootstrap__with_irrelevant_requirement(
        self, isolated_app: App
    ) -> None:
        plugin = DummyPluginDefinition("dependent", requires={lambda _: None})

        class _Owner(_HasPluginServices):
            plugins = PluginDefinitionsService(DummyPluginDefinition)

            def __init__(self):
                super().__init__(
                    services=ServiceLevel(plugins={DummyPluginDefinition: [plugin]})
                )
                type(self).plugins.add_init_plugins(self, plugin)

        async with _Owner() as owner:
            assert plugin in owner.plugins

    async def test_bootstrap__with_plugin_service_requirement(
        self, isolated_app: App
    ) -> None:
        class _Owner(_HasPluginServices):
            dependencies = PluginDefinitionsService(DummyPluginDefinition)
            dependents = PluginDefinitionsService(DummyPluginDefinition)

            def __init__(
                self,
                plugins: Iterable[ResolvablePluginDefinition[DummyPluginDefinition]],
                init_plugin: ResolvablePluginDefinition[DummyPluginDefinition],
            ):
                super().__init__(
                    services=ServiceLevel(plugins={DummyPluginDefinition: plugins})
                )
                type(self).dependents.add_init_plugins(self, init_plugin)

        dependency = DummyPluginDefinition("dependency")
        dependent = DummyPluginDefinition(
            "dependent", requires={_Owner.dependencies.require(dependency)}
        )
        owner = _Owner([dependent, dependency], dependent)
        async with owner:
            assert dependent in owner.dependents
            assert dependency in owner.dependencies

    async def test_bootstrap__with_supported_plugin_plugin_service_requirement(
        self, isolated_app: App
    ) -> None:
        class _Owner(_HasPluginServices):
            dependencies = PluginDefinitionsService(DummyPluginDefinition)
            dependents = PluginDefinitionsService(DummyPluginDefinition)

        dependency = DummyPluginDefinition("dependency")
        dependent = DummyPluginDefinition(
            "dependent", requires={_Owner.dependencies.require(dependency)}
        )
        owner = _Owner(
            services=ServiceLevel(
                plugins={DummyPluginDefinition: [dependent, dependency]},
            ),
            supported_plugins={dependent},
        )
        async with owner:
            assert dependent not in owner.dependents
            assert dependency in owner.dependencies


class PluginServiceManagerTestBase:
    _SERVICES: ClassVar[ServiceLevel] = ServiceLevel(
        plugins={
            DummyPluginDefinition: [
                DummyPluginOne,
                DummyPluginTwo,
                DummyPluginThree,
                DummyPluginWithLifeCycle,
            ]
        }
    )


class _PluginServiceManagerTestSut(
    PluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DummyPluginDefinition,
        Sequence[MachineName],
        ResolvablePluginDefinition[DummyPluginDefinition] | DummyPluginManufacturer,
    ]
):
    def __init__(self, *, auto: bool = True):
        super().__init__(DummyPluginDefinition, auto=auto)

    @override
    def new_service(
        self, owner: ResolvableServiceLevelHasPluginServices, /
    ) -> Sequence[MachineName]:
        raise NotImplementedError


class _PluginServiceManagerTestOwner(HasPluginServices, HasServiceLevel):
    my_first_service = _PluginServiceManagerTestSut()

    def __init__(self, *plugins: ResolvablePluginDefinition[DummyPluginDefinition]):
        super().__init__(services=ServiceLevel())
        type(self).my_first_service.add_init_plugins(self, *plugins)


class TestPluginServiceManager:
    def test_add_init_plugins(self) -> None:
        owner = _PluginServiceManagerTestOwner(
            DummyPluginOne.plugin(), DummyPluginTwo.plugin()
        )
        init_plugins = _PluginServiceManagerTestOwner.my_first_service.get_init_plugins(
            owner
        )
        assert tuple(init_plugins) == (DummyPluginOne.plugin(), DummyPluginTwo.plugin())

    def test_auto__without_auto(self) -> None:
        sut = _PluginServiceManagerTestSut(auto=False)
        assert not sut.auto

    def test_auto__with_auto(self) -> None:
        sut = _PluginServiceManagerTestSut(auto=True)
        assert sut.auto

    def test_get_init_plugins__without_plugins(self) -> None:
        assert not _PluginServiceManagerTestOwner.my_first_service.get_init_plugins(
            _PluginServiceManagerTestOwner()
        )

    async def test_get_init_plugins__with_plugins(self) -> None:
        owner = _PluginServiceManagerTestOwner(DummyPluginOne)
        assert _PluginServiceManagerTestOwner.my_first_service.get_init_plugins(
            owner
        ) == [DummyPluginOne]

    async def test_get_plugins__with_plugins(self) -> None:
        owner = _PluginServiceManagerTestOwner()
        await _PluginServiceManagerTestOwner.my_first_service.init_plugins(
            owner, DummyPluginOne
        )
        assert list(
            _PluginServiceManagerTestOwner.my_first_service.get_plugins(owner)
        ) == [DummyPluginOne]

    async def test_get_plugins__without_plugins(self) -> None:
        owner = _PluginServiceManagerTestOwner()
        await _PluginServiceManagerTestOwner.my_first_service.init_plugins(owner)
        assert not _PluginServiceManagerTestOwner.my_first_service.get_plugins(owner)

    def test_pre_init_owner(self) -> None:
        owner = _PluginServiceManagerTestOwner()
        assert not _PluginServiceManagerTestOwner.my_first_service.get_init_plugins(
            owner
        )

    async def test_init_plugins__without_plugins(self) -> None:
        owner = _PluginServiceManagerTestOwner()
        await _PluginServiceManagerTestOwner.my_first_service.init_plugins(owner)

    def test_override(self) -> None:
        machine_names = [MachineName("foo"), MachineName("bar")]

        class _Owner(_PluginServiceManagerTestOwner):
            def __init__(self):
                type(self).my_first_service.override(self, Service(machine_names))
                super().__init__()

        owner = _Owner()
        assert owner.my_first_service == machine_names

    def test_plugin_type(self) -> None:
        assert _PluginServiceManagerTestSut().plugin_type is DummyPluginDefinition

    async def test_prepare_plugins__without_plugins(self) -> None:
        assert (
            list(
                await _PluginServiceManagerTestSut().prepare_plugins(
                    _PluginServiceManagerTestOwner()
                )
            )
            == []
        )

    async def test_prepare_plugins__deduplicates(self) -> None:
        assert list(
            await _PluginServiceManagerTestSut().prepare_plugins(
                _PluginServiceManagerTestOwner(),
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
