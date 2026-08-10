from collections.abc import Sequence
from typing import override

import pytest

from betty.services.plugin import HasPluginServices
from betty.services.plugin.instance import ServicePluginInstance
from betty.services.plugin.instance.collection import (
    CollectionPluginInstanceServiceManager,
)
from betty.test_utils.plugin import (
    DummyPlugin,
    DummyPluginDefinition,
    DummyPluginManufacturer,
    DummyPluginWithLifeCycle,
)
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)


class _CollectionPluginInstanceServiceManagerTestSut(
    CollectionPluginInstanceServiceManager[
        HasPluginServices, DummyPluginDefinition, Sequence[DummyPlugin], DummyPlugin
    ]
):
    @override
    def new_service(self, owner: HasPluginServices, /) -> Sequence[DummyPlugin]:
        raise NotImplementedError


class TestCollectionPluginInstanceServiceManager(PluginServiceManagerTestBase):
    class Cls(HasPluginServices):
        my_first_service = _CollectionPluginInstanceServiceManagerTestSut(
            DummyPluginDefinition
        )

    @pytest.mark.parametrize(
        "init_plugin",
        [
            DummyPluginWithLifeCycle,
            DummyPluginWithLifeCycle.plugin(),
            DummyPluginManufacturer(DummyPluginWithLifeCycle),
        ],
    )
    async def test_new_service_item(
        self, init_plugin: ServicePluginInstance[DummyPluginDefinition]
    ) -> None:
        async with self.Cls(services=self._SERVICES) as service_provider:
            assert isinstance(
                await self.Cls.my_first_service.new_service_item(
                    service_provider, init_plugin
                ),
                DummyPluginWithLifeCycle,
            )
