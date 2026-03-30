from collections.abc import Sequence
from typing import override

from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import OrderedPluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition
from betty.service.level import ServiceLevel
from betty.service.plugin.service import PluginServiceProvider
from betty.service.plugin.service.collection import CollectionPluginServiceManager
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE
from betty.tests.service.plugin.service.test___init__ import (
    PluginServiceManagerTestBase,
)


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
        PluginServiceProvider,
        _DummyOrderedPluginDefinition,
        Sequence[_DummyOrderedPluginDefinition],
        _DummyOrderedPluginDefinition,
        ResolvablePluginDefinition[_DummyOrderedPluginDefinition],
    ]
):
    def __init__(self):
        super().__init__(_DummyOrderedPluginDefinition)

    @override
    def new_service(
        self, service_provider: PluginServiceProvider, /
    ) -> Sequence[_DummyOrderedPluginDefinition]:
        raise NotImplementedError

    @override
    def new_service_item(
        self,
        service_provider: PluginServiceProvider,
        plugin: ResolvablePluginDefinition[_DummyOrderedPluginDefinition],
        /,
    ) -> _DummyOrderedPluginDefinition:
        raise NotImplementedError


class _CollectionPluginServiceManagerTestServiceProvider(PluginServiceProvider):
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
        async with _CollectionPluginServiceManagerTestServiceProvider(
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
        ) as service_provider:
            assert list(
                await _CollectionPluginServiceManagerTestServiceProvider.my_first_service.prepare_plugins(
                    service_provider,
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
