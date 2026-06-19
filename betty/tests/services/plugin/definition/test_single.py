from betty.services.plugin import PluginServiceProvider
from betty.services.plugin.definition.single import PluginDefinitionService
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)


class TestPluginDefinitionService(PluginServiceManagerTestBase):
    class Cls(PluginServiceProvider):
        my_first_service = PluginDefinitionService(DummyPluginDefinition)

    async def test_new_service(self) -> None:
        service_provider = self.Cls(services=self._SERVICES)
        self.Cls.my_first_service.add_init_plugins(service_provider, DummyPluginOne)
        async with service_provider:
            assert service_provider.my_first_service is DummyPluginOne.plugin()
