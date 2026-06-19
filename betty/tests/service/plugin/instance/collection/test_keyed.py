from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.instance.collection.keyed import (
    PluginInstancesService,
)
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)
from betty.tests.service.test_plugin import (
    PluginServiceManagerTestBase,
)


class TestPluginInstancesService(PluginServiceManagerTestBase):
    class Cls(PluginServiceProvider):
        my_first_service = PluginInstancesService(DummyPluginDefinition)

    async def test_new_service__without_plugins(self) -> None:
        async with self.Cls(services=self._SERVICES) as service_provider:
            assert not service_provider.my_first_service

    async def test_new_service__with_plugins(self) -> None:
        service_provider = self.Cls(services=self._SERVICES)
        self.Cls.my_first_service.add_init_plugins(
            service_provider, DummyPluginOne, DummyPluginTwo
        )
        async with service_provider:
            assert DummyPluginOne in service_provider.my_first_service
            assert DummyPluginTwo in service_provider.my_first_service
            assert DummyPluginThree not in service_provider.my_first_service
