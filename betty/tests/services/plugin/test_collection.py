from collections.abc import Sequence
from typing import override

from betty.definition import ResolvableDefinition
from betty.definition.id import resolve_id
from betty.machine_name import MachineName
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import OrderedPluginDefinition
from betty.service_level import HasServiceLevel, ServiceLevel
from betty.services.plugin import (
    HasPluginServices,
    ResolvableServiceLevelHasPluginServices,
)
from betty.services.plugin.collection import CollectionPluginServiceManager
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE
from betty.tests.services.test_plugin import (
    PluginServiceManagerTestBase,
)
from betty.typing import Unreachable


@PluginTypeDefinition(
    "dummy-plugin",
    label="dummy plugin",
    label_plural="dummy plugin",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _DummyOrderedPluginDefinition(OrderedPluginDefinition):
    pass


class _CollectionPluginServiceManagerTestSut(
    CollectionPluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        _DummyOrderedPluginDefinition,
        Sequence[_DummyOrderedPluginDefinition],
        _DummyOrderedPluginDefinition,
        ResolvableDefinition[_DummyOrderedPluginDefinition],
    ]
):
    def __init__(self):
        super().__init__(_DummyOrderedPluginDefinition)

    @override
    def new_service(
        self, owner: HasPluginServices, /
    ) -> Sequence[_DummyOrderedPluginDefinition]:
        raise Unreachable

    @override
    def new_service_item(
        self,
        owner: HasPluginServices,
        plugin: ResolvableDefinition[_DummyOrderedPluginDefinition],
        /,
    ) -> _DummyOrderedPluginDefinition:
        raise Unreachable

    @override
    def resolve_init_plugin_id(
        self,
        plugin: ResolvableDefinition[_DummyOrderedPluginDefinition],
        /,
    ) -> MachineName:
        return resolve_id(plugin)


class _CollectionPluginServiceManagerTestOwner(HasPluginServices, HasServiceLevel):
    my_first_service = _CollectionPluginServiceManagerTestSut()


class TestCollectionPluginServiceManager(PluginServiceManagerTestBase):
    async def test_prepare_plugins(self) -> None:
        before_center = _DummyOrderedPluginDefinition(
            "before-center", before={"center"}
        )
        center = _DummyOrderedPluginDefinition("center")
        after_center = _DummyOrderedPluginDefinition("after-center", after={"center"})
        after_center_2 = _DummyOrderedPluginDefinition(
            "after-center-2", after={"center"}
        )
        owner = _CollectionPluginServiceManagerTestOwner(
            services=ServiceLevel(
                plugins={
                    _DummyOrderedPluginDefinition: (
                        after_center_2,
                        after_center,
                        center,
                        before_center,
                    )
                }
            )
        )
        async with owner:
            assert list(
                await _CollectionPluginServiceManagerTestOwner.my_first_service.prepare_plugins(
                    owner,
                    after_center_2,
                    after_center,
                    center,
                    before_center,
                )
            ) == [
                before_center,
                center,
                after_center,
                after_center_2,
            ]
