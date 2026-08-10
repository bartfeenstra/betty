from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.collection.keyed import (
    PluginDefinitionsService,
)
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)


class TestPluginDefinitionsService(PluginServiceManagerTestBase):
    class Cls(HasPluginServices):
        my_first_service = PluginDefinitionsService(DummyPluginDefinition)

    async def test_new_service__without_plugin_definitions(self) -> None:
        async with self.Cls(services=self._SERVICES) as service_provider:
            assert not service_provider.my_first_service

    async def test_new_service__with_plugin_definitions(self) -> None:
        owner = self.Cls(services=self._SERVICES)
        self.Cls.my_first_service.add_init_plugins(
            owner, DummyPluginOne, DummyPluginTwo
        )
        async with owner:
            assert DummyPluginOne in owner.my_first_service
            assert DummyPluginTwo in owner.my_first_service
            assert DummyPluginThree not in owner.my_first_service
