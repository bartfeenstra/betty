from typing import override

from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
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


class _KeyedCollectionPluginServiceManagerTestOwner(HasPluginServices):
    my_first_service = _KeyedCollectionPluginServiceManagerTestSut()


class TestKeyedCollectionPluginServiceManager(PluginServiceManagerTestBase):
    async def test_new_service(self) -> None:
        owner = _KeyedCollectionPluginServiceManagerTestOwner(services=self._SERVICES)
        _KeyedCollectionPluginServiceManagerTestOwner.my_first_service.add_init_plugins(
            owner, DummyPluginThree, DummyPluginTwo, DummyPluginOne
        )
        async with owner:
            assert owner.my_first_service[DummyPluginOne] is DummyPluginOne.plugin()
