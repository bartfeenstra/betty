from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.single import PluginDefinitionService
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)


class TestPluginDefinitionService(PluginServiceManagerTestBase):
    class Cls(HasPluginServices):
        my_first_service = PluginDefinitionService(DummyPluginDefinition)

    async def test_new_service(self) -> None:
        owner = self.Cls(services=self._SERVICES)
        self.Cls.my_first_service.add_init_plugins(owner, DummyPluginOne)
        async with owner:
            assert owner.my_first_service is DummyPluginOne.plugin()
