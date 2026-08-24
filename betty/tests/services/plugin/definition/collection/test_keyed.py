from betty.plugin.resolve import ResolvablePluginDefinition
from betty.service_level import HasServiceLevel
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
    class _Owner(HasPluginServices, HasServiceLevel):
        my_first_service = PluginDefinitionsService(DummyPluginDefinition)

        def __init__(
            self, *init_plugins: ResolvablePluginDefinition[DummyPluginDefinition]
        ):
            super().__init__(services=TestPluginDefinitionsService._SERVICES)
            type(self).my_first_service.add_init_plugins(self, *init_plugins)

    async def test_new_service__without_plugin_definitions(self) -> None:
        owner = self._Owner()
        async with owner:
            assert not owner.my_first_service

    async def test_new_service__with_plugin_definitions(self) -> None:
        owner = self._Owner(DummyPluginOne, DummyPluginTwo)
        async with owner:
            assert DummyPluginOne in owner.my_first_service
            assert DummyPluginTwo in owner.my_first_service
            assert DummyPluginThree not in owner.my_first_service
