from collections.abc import Sequence
from typing import override

import pytest

from betty.definition import ResolvableDefinition, resolve_definition
from betty.definition.id import resolve_id
from betty.machine_name import MachineName
from betty.requirements.service import UnmetServiceRequirement
from betty.service_level import DownstreamServiceLevel, ServiceLevel
from betty.services.plugin import (
    HasPluginServices,
    PluginServiceManager,
    PluginServiceRequirement,
    ResolvableServiceLevelHasPluginServices,
)
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)


class _PluginServiceRequirementTestPluginServiceManager(
    PluginServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DummyPluginDefinition,
        Sequence[DummyPluginDefinition],
        DummyPluginDefinition,
    ]
):
    def __init__(self, *, auto: bool = False):
        super().__init__(DummyPluginDefinition, auto=auto)

    @override
    def new_service(
        self, owner: ResolvableServiceLevelHasPluginServices, /
    ) -> Sequence[DummyPluginDefinition]:
        return tuple(map(resolve_definition, self.get_init_plugins(owner)))

    @override
    def resolve_init_plugin_id(
        self,
        plugin: ResolvableDefinition[DummyPluginDefinition],
        /,
    ) -> MachineName:
        return resolve_id(plugin)


class _PluginServiceRequirementTestServices(ServiceLevel, HasPluginServices):
    def __init__(self, *my_first_plugins: ResolvableDefinition[DummyPluginDefinition]):
        super().__init__(
            plugins={
                DummyPluginDefinition: (
                    DummyPluginOne,
                    DummyPluginTwo,
                    DummyPluginThree,
                )
            }
        )
        type(self).my_first_plugins.add_init_plugins(self, *my_first_plugins)

    my_first_plugins = _PluginServiceRequirementTestPluginServiceManager()


class TestPluginServiceRequirement:
    async def test___call____without_required_service(self) -> None:

        sut = PluginServiceRequirement(
            _PluginServiceRequirementTestServices.my_first_plugins
        )
        with pytest.raises(UnmetServiceRequirement):
            await sut(ServiceLevel())

    async def test___call____with_upstream_without_required_service(self) -> None:
        sut = PluginServiceRequirement(
            _PluginServiceRequirementTestServices.my_first_plugins
        )
        with pytest.raises(UnmetServiceRequirement):
            await sut(DownstreamServiceLevel(upstream=ServiceLevel()))

    async def test___call____with_required_service_without_required_plugin(
        self,
    ) -> None:
        sut = PluginServiceRequirement(
            _PluginServiceRequirementTestServices.my_first_plugins, DummyPluginOne
        )
        services = _PluginServiceRequirementTestServices()
        async with services:
            with pytest.raises(UnmetServiceRequirement):
                await sut(services)

    async def test___call____with_required_service_with_required_plugin(self) -> None:
        sut = PluginServiceRequirement(
            _PluginServiceRequirementTestServices.my_first_plugins, DummyPluginOne
        )
        services = _PluginServiceRequirementTestServices(DummyPluginOne.definition)
        async with services:
            assert DummyPluginOne.definition in await sut(services)

    async def test___call____with_upstream_required_service_without_required_plugin(
        self,
    ) -> None:
        sut = PluginServiceRequirement(
            _PluginServiceRequirementTestServices.my_first_plugins, DummyPluginOne
        )
        services = _PluginServiceRequirementTestServices()
        async with services:
            with pytest.raises(UnmetServiceRequirement):
                await sut(DownstreamServiceLevel(upstream=services))

    async def test___call____with_upstream_required_service_with_required_plugin(
        self,
    ) -> None:
        sut = PluginServiceRequirement(
            _PluginServiceRequirementTestServices.my_first_plugins, DummyPluginOne
        )
        services = _PluginServiceRequirementTestServices(DummyPluginOne.definition)
        async with services:
            assert DummyPluginOne.definition in await sut(
                DownstreamServiceLevel(upstream=services)
            )

    def test_plugins__without_plugins(self) -> None:
        service = _PluginServiceRequirementTestPluginServiceManager()
        sut = PluginServiceRequirement(service)
        assert not sut.plugins

    def test_plugins__with_plugins(self) -> None:
        service = _PluginServiceRequirementTestPluginServiceManager()
        plugins = [DummyPluginOne.definition, DummyPluginTwo.definition]
        sut = PluginServiceRequirement(service, *plugins)
        assert list(sut.plugins) == plugins

    def test_service(self) -> None:
        service = _PluginServiceRequirementTestPluginServiceManager()
        sut = PluginServiceRequirement(service)
        assert sut.service is service
