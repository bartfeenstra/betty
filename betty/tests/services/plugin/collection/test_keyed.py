from typing import override

from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.service_level import ServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.collection.keyed import (
    KeyedCollectionPluginServiceManager,
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


class _KeyedCollectionPluginServiceManagerTestSut(
    KeyedCollectionPluginServiceManager[
        HasPluginServices,
        DummyPluginDefinition,
        DummyPluginDefinition,
        ResolvablePluginDefinition[DummyPluginDefinition],
    ]
):
    def __init__(self):
        super().__init__(DummyPluginDefinition)

    @override
    def new_service_item(
        self,
        owner: HasPluginServices,
        plugin: ResolvablePluginDefinition[DummyPluginDefinition],
        /,
    ) -> DummyPluginDefinition:
        return resolve_plugin_definition(plugin)


class TestKeyedCollectionPluginServiceManager(PluginServiceManagerTestBase):
    async def test_new_service(self) -> None:
        owner = _KeyedCollectionPluginServiceManagerTestOwner()
        async with owner:
            assert owner.my_first_service[DummyPluginOne] is DummyPluginOne.plugin()


class _KeyedCollectionPluginServiceManagerTestOwner(HasPluginServices, ServiceLevel):
    my_first_service = _KeyedCollectionPluginServiceManagerTestSut()

    def __init__(self):
        super().__init__(services=TestKeyedCollectionPluginServiceManager._SERVICES)
        type(self).my_first_service.add_init_plugins(
            self, DummyPluginThree, DummyPluginTwo, DummyPluginOne
        )
