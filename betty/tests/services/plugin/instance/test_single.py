import pytest

from betty.service_level import HasServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.instance import ServicePluginInstance
from betty.services.plugin.instance.single import PluginInstanceService
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginManufacturer,
    DummyPluginWithLifeCycle,
)
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)


class TestPluginInstanceService(PluginServiceManagerTestBase):
    class _Owner(HasPluginServices, HasServiceLevel):
        my_first_service = PluginInstanceService(DummyPluginDefinition)

        def __init__(self, init_plugin: ServicePluginInstance[DummyPluginDefinition]):
            super().__init__(services=TestPluginInstanceService._SERVICES)
            type(self).my_first_service.add_init_plugins(self, init_plugin)

    @pytest.mark.parametrize(
        "init_plugin",
        [
            DummyPluginWithLifeCycle,
            DummyPluginWithLifeCycle.plugin(),
            DummyPluginManufacturer(DummyPluginWithLifeCycle),
        ],
    )
    async def test_new_service(
        self, init_plugin: ServicePluginInstance[DummyPluginDefinition]
    ) -> None:
        owner = self._Owner(init_plugin)
        async with owner:
            plugin = await owner.my_first_service
            assert plugin.bootstrapped
        assert plugin.shut_down
