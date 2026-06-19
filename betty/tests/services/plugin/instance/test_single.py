import pytest

from betty.services.plugin import PluginServiceProvider
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
    class Cls(PluginServiceProvider):
        my_first_service = PluginInstanceService(DummyPluginDefinition)

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
        service_provider = self.Cls(services=self._SERVICES)
        self.Cls.my_first_service.add_init_plugins(service_provider, init_plugin)
        async with service_provider:
            plugin = await service_provider.my_first_service
            assert plugin.bootstrapped
        assert plugin.shut_down
