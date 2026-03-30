from betty.service.plugin.service import PluginServiceProvider
from betty.service.plugin.service.definition.collection.keyed import (
    PluginDefinitionsService,
)
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)
from betty.tests.service.plugin.service.test___init__ import (
    PluginServiceManagerTestBase,
)


class TestPluginDefinitionsService(PluginServiceManagerTestBase):
    class Cls(PluginServiceProvider):
        my_first_service = PluginDefinitionsService(DummyPluginDefinition)

    async def test_new_service__without_plugin_definitions(self) -> None:
        async with self.Cls(services=self._SERVICES) as service_provider:
            assert not service_provider.my_first_service

    async def test_new_service__with_plugin_definitions(self) -> None:
        service_provider = self.Cls(services=self._SERVICES)
        self.Cls.my_first_service.add_init_plugins(
            service_provider, DummyPluginOne, DummyPluginTwo
        )
        async with service_provider:
            assert DummyPluginOne in service_provider.my_first_service
            assert DummyPluginTwo in service_provider.my_first_service
            assert DummyPluginThree not in service_provider.my_first_service
