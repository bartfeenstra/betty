from collections.abc import Sequence
from typing import override

import pytest

from betty.plugin.resolve import ResolvablePluginDefinition
from betty.service_level import ServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.collection import (
    CollectionPluginDefinitionServiceManager,
)
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginWithLifeCycle,
)
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)


class _CollectionPluginDefinitionServiceManagerTestSut(
    CollectionPluginDefinitionServiceManager[
        HasPluginServices, DummyPluginDefinition, Sequence[DummyPluginDefinition]
    ]
):
    @override
    def new_service(
        self, owner: HasPluginServices, /
    ) -> Sequence[DummyPluginDefinition]:
        raise NotImplementedError


class TestCollectionPluginDefinitionServiceManager(PluginServiceManagerTestBase):
    class _Owner(HasPluginServices, ServiceLevel):
        my_first_service = _CollectionPluginDefinitionServiceManagerTestSut(
            DummyPluginDefinition
        )

    @pytest.mark.parametrize(
        "init_plugin",
        [
            DummyPluginWithLifeCycle,
            DummyPluginWithLifeCycle.plugin(),
        ],
    )
    async def test_new_service_item(
        self, init_plugin: ResolvablePluginDefinition[DummyPluginDefinition]
    ) -> None:
        owner = self._Owner(services=self._SERVICES)
        async with owner:
            assert (
                self._Owner.my_first_service.new_service_item(owner, init_plugin)
                is DummyPluginWithLifeCycle.plugin()
            )
