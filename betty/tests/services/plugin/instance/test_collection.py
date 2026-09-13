from collections.abc import Sequence
from typing import override

import pytest

from betty.service_level import HasServiceLevel
from betty.services.plugin import (
    HasPluginServices,
    ResolvableServiceLevelHasPluginServices,
)
from betty.services.plugin.instance.collection import (
    CollectionPluginInstanceServiceManager,
)
from betty.test_utils.plugin import (
    DummyPlugin,
    DummyPluginDefinition,
    DummyPluginWithLifeCycle,
    ManufacturableDummyPlugin,
    NewDummyPlugin,
)
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)
from betty.typing import Unreachable


class _CollectionPluginInstanceServiceManagerTestSut(
    CollectionPluginInstanceServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DummyPluginDefinition,
        Sequence[DummyPlugin],
        NewDummyPlugin,
        DummyPlugin,
    ]
):
    @override
    def new_service(self, owner: HasPluginServices, /) -> Sequence[DummyPlugin]:
        raise Unreachable


class TestCollectionPluginInstanceServiceManager(PluginServiceManagerTestBase):
    class _Owner(HasPluginServices, HasServiceLevel):
        my_first_service = _CollectionPluginInstanceServiceManagerTestSut(
            DummyPluginDefinition
        )

    @pytest.mark.parametrize(
        "init_plugin",
        [
            DummyPluginWithLifeCycle,
            DummyPluginWithLifeCycle.plugin(),
            NewDummyPlugin(DummyPluginWithLifeCycle),
        ],
    )
    async def test_new_service_item(
        self, init_plugin: ManufacturableDummyPlugin
    ) -> None:
        owner = self._Owner(services=self._SERVICES)
        async with owner:
            assert isinstance(
                await self._Owner.my_first_service.new_service_item(owner, init_plugin),
                DummyPluginWithLifeCycle,
            )
