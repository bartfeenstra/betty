from typing import override

from betty.definition import ResolvableDefinition, resolve_definition
from betty.definition.id import resolve_id
from betty.machine_name import MachineName
from betty.service_level import HasServiceLevel
from betty.services.plugin import (
    HasPluginServices,
    ResolvableServiceLevelHasPluginServices,
)
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
        ResolvableServiceLevelHasPluginServices,
        DummyPluginDefinition,
        DummyPluginDefinition,
        ResolvableDefinition[DummyPluginDefinition],
    ]
):
    def __init__(self):
        super().__init__(DummyPluginDefinition)

    @override
    def new_service_item(
        self,
        owner: HasPluginServices,
        plugin: ResolvableDefinition[DummyPluginDefinition],
        /,
    ) -> DummyPluginDefinition:
        return resolve_definition(plugin)

    @override
    def resolve_init_plugin_id(
        self,
        plugin: ResolvableDefinition[DummyPluginDefinition],
        /,
    ) -> MachineName:
        return resolve_id(plugin)


class TestKeyedCollectionPluginServiceManager(PluginServiceManagerTestBase):
    async def test_new_service(self) -> None:
        owner = _KeyedCollectionPluginServiceManagerTestOwner()
        async with owner:
            assert owner.my_first_service[DummyPluginOne] is DummyPluginOne.definition


class _KeyedCollectionPluginServiceManagerTestOwner(HasPluginServices, HasServiceLevel):
    my_first_service = _KeyedCollectionPluginServiceManagerTestSut()

    def __init__(self):
        super().__init__(services=TestKeyedCollectionPluginServiceManager._SERVICES)
        type(self).my_first_service.add_init_plugins(
            self, DummyPluginThree, DummyPluginTwo, DummyPluginOne
        )
