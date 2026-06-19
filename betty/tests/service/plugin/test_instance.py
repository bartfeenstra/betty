from typing import override

import pytest

from betty.requirements.service import UnmetServiceRequirement
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.instance import (
    PluginInstanceServiceManager,
    ServicePluginInstance,
)
from betty.service_level import ServiceLevel
from betty.test_utils.plugin import (
    DummyPlugin,
    DummyPluginDefinition,
    DummyPluginManufacturer,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
    DummyPluginWithLifeCycle,
)
from betty.tests.service.test_plugin import (
    PluginServiceManagerTestBase,
)


class _PluginInstanceServiceManagerTestSut(
    PluginInstanceServiceManager[
        PluginServiceProvider, DummyPluginDefinition, DummyPlugin, DummyPlugin
    ]
):
    def __init__(self):
        super().__init__(DummyPluginDefinition)

    @override
    def new_service(self, service_provider: PluginServiceProvider, /) -> DummyPlugin:
        raise NotImplementedError


class _PluginInstanceServiceManagerTestServiceProvider(PluginServiceProvider):
    my_first_service = _PluginInstanceServiceManagerTestSut()


class TestPluginInstanceServiceManager(PluginServiceManagerTestBase):
    @pytest.mark.parametrize(
        "item",
        [
            DummyPluginOne,
            DummyPluginOne.plugin(),
            DummyPluginManufacturer(DummyPluginOne),
        ],
    )
    async def test_new_plugin_instance_service_item(
        self, item: ServicePluginInstance
    ) -> None:
        async with _PluginInstanceServiceManagerTestServiceProvider(
            services=self._SERVICES
        ) as service_provider:
            service_item = _PluginInstanceServiceManagerTestServiceProvider.my_first_service.new_plugin_instance_service_item(
                service_provider, item
            )
            plugin = await service_item
            assert isinstance(plugin, DummyPluginOne)
            assert await service_item is plugin

    @pytest.mark.parametrize(
        "item",
        [
            DummyPluginWithLifeCycle,
            DummyPluginWithLifeCycle.plugin(),
            DummyPluginManufacturer(DummyPluginWithLifeCycle),
        ],
    )
    async def test_new_plugin_instance_service_item__with_life_cycle(
        self, item: ServicePluginInstance
    ) -> None:
        async with _PluginInstanceServiceManagerTestServiceProvider(
            services=self._SERVICES
        ) as service_provider:
            service_item = _PluginInstanceServiceManagerTestServiceProvider.my_first_service.new_plugin_instance_service_item(
                service_provider, item
            )
            plugin = await service_item
            assert isinstance(plugin, DummyPluginWithLifeCycle)
            assert await service_item is plugin
            assert plugin.bootstrapped
        assert plugin.shut_down

    async def test_prepare_plugins(self) -> None:
        manufacturer_one = DummyPluginManufacturer(DummyPluginOne)
        manufacturer_two = DummyPluginManufacturer(DummyPluginTwo)
        manufacturer_three = DummyPluginManufacturer(DummyPluginThree)
        assert list(
            await _PluginInstanceServiceManagerTestServiceProvider.my_first_service.prepare_plugins(
                _PluginInstanceServiceManagerTestServiceProvider(
                    services=ServiceLevel()
                ),
                DummyPluginOne,
                manufacturer_one,
                DummyPluginOne,
                DummyPluginTwo,
                manufacturer_two,
                manufacturer_three,
                DummyPluginThree,
            )
        ) == [manufacturer_one, manufacturer_two, manufacturer_three]

    async def test_prepare_plugins__with_duplicate_manufacturers(self) -> None:
        with pytest.raises(UnmetServiceRequirement):
            await _PluginInstanceServiceManagerTestServiceProvider.my_first_service.prepare_plugins(
                _PluginInstanceServiceManagerTestServiceProvider(
                    services=ServiceLevel()
                ),
                DummyPluginManufacturer(DummyPluginOne),
                DummyPluginManufacturer(DummyPluginOne),
            )

    def test_resolve_init_plugin_id__with_plugin_manufacturer(self) -> None:
        assert (
            _PluginInstanceServiceManagerTestSut().resolve_init_plugin_id(
                DummyPluginManufacturer(DummyPluginOne)
            )
            == DummyPluginOne.plugin().id
        )
