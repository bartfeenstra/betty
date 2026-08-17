from betty.service_level import ServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.single import PluginDefinitionService
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)


class TestPluginDefinitionService(PluginServiceManagerTestBase):
    class _Owner(HasPluginServices, ServiceLevel):
        my_first_service = PluginDefinitionService(DummyPluginDefinition)

        def __init__(self):
            super().__init__(services=TestPluginDefinitionService._SERVICES)
            type(self).my_first_service.add_init_plugins(self, DummyPluginOne)

    async def test_new_service(self) -> None:
        owner = self._Owner()
        async with owner:
            assert owner.my_first_service is DummyPluginOne.plugin()
