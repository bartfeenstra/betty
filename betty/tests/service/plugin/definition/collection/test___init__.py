from collections.abc import Sequence
from typing import override

import pytest

from betty.plugin.resolve import ResolvablePluginDefinition
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.definition.collection import (
    CollectionPluginDefinitionServiceManager,
)
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginWithLifeCycle,
)
from betty.tests.service.plugin.test___init__ import (
    PluginServiceManagerTestBase,
)


class _CollectionPluginDefinitionServiceManagerTestSut(
    CollectionPluginDefinitionServiceManager[
        PluginServiceProvider, DummyPluginDefinition, Sequence[DummyPluginDefinition]
    ]
):
    @override
    def new_service(
        self, service_provider: PluginServiceProvider, /
    ) -> Sequence[DummyPluginDefinition]:
        raise NotImplementedError


class TestCollectionPluginDefinitionServiceManager(PluginServiceManagerTestBase):
    class Cls(PluginServiceProvider):
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
        async with self.Cls(services=self._SERVICES) as service_provider:
            assert (
                self.Cls.my_first_service.new_service_item(
                    service_provider, init_plugin
                )
                is DummyPluginWithLifeCycle.plugin()
            )
