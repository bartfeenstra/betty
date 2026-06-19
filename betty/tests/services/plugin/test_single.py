from typing import override

import pytest

from betty.plugin.resolve import ResolvablePluginDefinition
from betty.requirements.service import UnmetServiceRequirement
from betty.service_level import ServiceLevel
from betty.services.plugin import PluginServiceProvider
from betty.services.plugin.single import SinglePluginServiceManager
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginTwo,
)


class _SinglePluginServiceManagerTestSut(
    SinglePluginServiceManager[
        PluginServiceProvider,
        DummyPluginDefinition,
        DummyPluginDefinition,
        ResolvablePluginDefinition[DummyPluginDefinition],
    ]
):
    def __init__(self):
        super().__init__(DummyPluginDefinition)

    @override
    def new_service(
        self, service_provider: PluginServiceProvider, /
    ) -> DummyPluginDefinition:
        raise NotImplementedError


class _SinglePluginServiceManagerTestServiceProvider(PluginServiceProvider):
    my_first_service = _SinglePluginServiceManagerTestSut()


class TestSinglePluginServiceManager:
    async def test_prepare_plugins__without_plugins(self) -> None:
        with pytest.raises(UnmetServiceRequirement):
            await _SinglePluginServiceManagerTestServiceProvider.my_first_service.prepare_plugins(
                _SinglePluginServiceManagerTestServiceProvider(services=ServiceLevel())
            )

    async def test_prepare_plugins__with_one_plugin(self) -> None:
        assert list(
            await _SinglePluginServiceManagerTestServiceProvider.my_first_service.prepare_plugins(
                _SinglePluginServiceManagerTestServiceProvider(services=ServiceLevel()),
                DummyPluginOne,
            )
        ) == [DummyPluginOne]

    async def test_prepare_plugins__with_one_plugin_with_duplicates(self) -> None:
        assert list(
            await _SinglePluginServiceManagerTestServiceProvider.my_first_service.prepare_plugins(
                _SinglePluginServiceManagerTestServiceProvider(services=ServiceLevel()),
                DummyPluginOne,
                DummyPluginOne.plugin(),
            )
        ) == [DummyPluginOne.plugin()]

    async def test_prepare_plugins__with_multiple_plugins(self) -> None:
        with pytest.raises(UnmetServiceRequirement):
            await _SinglePluginServiceManagerTestServiceProvider.my_first_service.prepare_plugins(
                _SinglePluginServiceManagerTestServiceProvider(services=ServiceLevel()),
                DummyPluginOne,
                DummyPluginTwo,
            )
