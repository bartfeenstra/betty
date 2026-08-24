from typing import override

import pytest

from betty.plugin.resolve import ResolvablePluginDefinition
from betty.requirements.service import UnmetServiceRequirement
from betty.service_level import HasServiceLevel, ServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.single import SinglePluginServiceManager
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginTwo,
)


class _SinglePluginServiceManagerTestSut(
    SinglePluginServiceManager[
        HasPluginServices,
        DummyPluginDefinition,
        DummyPluginDefinition,
        ResolvablePluginDefinition[DummyPluginDefinition],
    ]
):
    def __init__(self):
        super().__init__(DummyPluginDefinition)

    @override
    def new_service(self, owner: HasPluginServices, /) -> DummyPluginDefinition:
        raise NotImplementedError


class _SinglePluginServiceManagerTestOwner(HasPluginServices, HasServiceLevel):
    my_first_service = _SinglePluginServiceManagerTestSut()


class TestSinglePluginServiceManager:
    async def test_prepare_plugins__without_plugins(self) -> None:
        with pytest.raises(UnmetServiceRequirement):
            await _SinglePluginServiceManagerTestOwner.my_first_service.prepare_plugins(
                _SinglePluginServiceManagerTestOwner(services=ServiceLevel())
            )

    async def test_prepare_plugins__with_one_plugin(self) -> None:
        assert list(
            await _SinglePluginServiceManagerTestOwner.my_first_service.prepare_plugins(
                _SinglePluginServiceManagerTestOwner(services=ServiceLevel()),
                DummyPluginOne,
            )
        ) == [DummyPluginOne]

    async def test_prepare_plugins__with_one_plugin_with_duplicates(self) -> None:
        assert list(
            await _SinglePluginServiceManagerTestOwner.my_first_service.prepare_plugins(
                _SinglePluginServiceManagerTestOwner(services=ServiceLevel()),
                DummyPluginOne,
                DummyPluginOne.plugin(),
            )
        ) == [DummyPluginOne.plugin()]

    async def test_prepare_plugins__with_multiple_plugins(self) -> None:
        with pytest.raises(UnmetServiceRequirement):
            await _SinglePluginServiceManagerTestOwner.my_first_service.prepare_plugins(
                _SinglePluginServiceManagerTestOwner(services=ServiceLevel()),
                DummyPluginOne,
                DummyPluginTwo,
            )
