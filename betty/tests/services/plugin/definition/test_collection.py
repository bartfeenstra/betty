from collections.abc import Sequence
from typing import override

import pytest

from betty.definition import ResolvableDefinition
from betty.service_level import HasServiceLevel
from betty.services.plugin import (
    HasPluginServices,
    ResolvableServiceLevelHasPluginServices,
)
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
from betty.typing import Unreachable


class _CollectionPluginDefinitionServiceManagerTestSut(
    CollectionPluginDefinitionServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DummyPluginDefinition,
        Sequence[DummyPluginDefinition],
    ]
):
    @override
    def new_service(
        self, owner: HasPluginServices, /
    ) -> Sequence[DummyPluginDefinition]:
        raise Unreachable


class TestCollectionPluginDefinitionServiceManager(PluginServiceManagerTestBase):
    class _Owner(HasPluginServices, HasServiceLevel):
        my_first_service = _CollectionPluginDefinitionServiceManagerTestSut(
            DummyPluginDefinition
        )

    @pytest.mark.parametrize(
        "init_plugin",
        [
            DummyPluginWithLifeCycle,
            DummyPluginWithLifeCycle.definition,
        ],
    )
    async def test_new_service_item(
        self, init_plugin: ResolvableDefinition[DummyPluginDefinition]
    ) -> None:
        owner = self._Owner(services=self._SERVICES)
        async with owner:
            assert (
                self._Owner.my_first_service.new_service_item(owner, init_plugin)
                is DummyPluginWithLifeCycle.definition
            )
