from typing import override

import pytest

from betty.requirements.service import UnmetServiceRequirement
from betty.service_level import ServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.instance import (
    PluginInstanceServiceManager,
    ServicePluginInstance,
)
from betty.test_utils.plugin import (
    DummyPlugin,
    DummyPluginDefinition,
    DummyPluginManufacturer,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
    DummyPluginWithLifeCycle,
)
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)


class _PluginInstanceServiceManagerTestSut(
    PluginInstanceServiceManager[
        HasPluginServices, DummyPluginDefinition, DummyPlugin, DummyPlugin
    ]
):
    def __init__(self):
        super().__init__(DummyPluginDefinition)

    @override
    def new_service(self, owner: HasPluginServices, /) -> DummyPlugin:
        raise NotImplementedError


class _PluginInstanceServiceManagerTestOwner(HasPluginServices):
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
        owner = _PluginInstanceServiceManagerTestOwner(services=self._SERVICES)
        async with owner:
            service_item = _PluginInstanceServiceManagerTestOwner.my_first_service.new_plugin_instance_service_item(
                owner, item
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
        owner = _PluginInstanceServiceManagerTestOwner(services=self._SERVICES)
        async with owner:
            service_item = _PluginInstanceServiceManagerTestOwner.my_first_service.new_plugin_instance_service_item(
                owner, item
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
            await _PluginInstanceServiceManagerTestOwner.my_first_service.prepare_plugins(
                _PluginInstanceServiceManagerTestOwner(services=ServiceLevel()),
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
            await (
                _PluginInstanceServiceManagerTestOwner.my_first_service.prepare_plugins(
                    _PluginInstanceServiceManagerTestOwner(services=ServiceLevel()),
                    DummyPluginManufacturer(DummyPluginOne),
                    DummyPluginManufacturer(DummyPluginOne),
                )
            )

    def test_resolve_init_plugin_id__with_plugin_manufacturer(self) -> None:
        assert (
            _PluginInstanceServiceManagerTestSut().resolve_init_plugin_id(
                DummyPluginManufacturer(DummyPluginOne)
            )
            == DummyPluginOne.plugin().id
        )
