from betty.service_level import HasServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.instance import ServicePluginInstance
from betty.services.plugin.instance.collection.keyed import PluginInstancesService
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)


class TestPluginInstancesService(PluginServiceManagerTestBase):
    class _Owner(HasPluginServices, HasServiceLevel):
        my_first_service = PluginInstancesService(DummyPluginDefinition)

        def __init__(self, *init_plugins: ServicePluginInstance[DummyPluginDefinition]):
            super().__init__(services=TestPluginInstancesService._SERVICES)
            type(self).my_first_service.add_init_plugins(self, *init_plugins)

    async def test_new_service__without_plugins(self) -> None:
        owner = self._Owner()
        async with owner:
            assert not owner.my_first_service

    async def test_new_service__with_plugins(self) -> None:
        owner = self._Owner(DummyPluginOne, DummyPluginTwo)
        async with owner:
            assert DummyPluginOne in owner.my_first_service
            assert DummyPluginTwo in owner.my_first_service
            assert DummyPluginThree not in owner.my_first_service
