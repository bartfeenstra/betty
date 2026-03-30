from typing import override

from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.service.plugin.service import PluginServiceProvider
from betty.service.plugin.service.collection.keyed import (
    KeyedCollectionPluginServiceManager,
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


class _KeyedCollectionPluginServiceManagerTestSut(
    KeyedCollectionPluginServiceManager[
        PluginServiceProvider,
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
        service_provider: PluginServiceProvider,
        plugin: ResolvablePluginDefinition[DummyPluginDefinition],
        /,
    ) -> DummyPluginDefinition:
        return resolve_plugin_definition(plugin)


class _KeyedCollectionPluginServiceManagerTestServiceProvider(PluginServiceProvider):
    my_first_service = _KeyedCollectionPluginServiceManagerTestSut()


class TestKeyedCollectionPluginServiceManager(PluginServiceManagerTestBase):
    async def test_new_service(self) -> None:
        service_provider = _KeyedCollectionPluginServiceManagerTestServiceProvider(
            services=self._SERVICES
        )
        _KeyedCollectionPluginServiceManagerTestServiceProvider.my_first_service.add_init_plugins(
            service_provider, DummyPluginThree, DummyPluginTwo, DummyPluginOne
        )
        async with service_provider:
            assert (
                service_provider.my_first_service[DummyPluginOne]
                is DummyPluginOne.plugin()
            )
