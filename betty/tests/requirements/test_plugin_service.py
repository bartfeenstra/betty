from collections.abc import Sequence
from typing import override

import pytest

from betty.plugin.resolve import resolve_plugin_definition
from betty.requirements.service import UnmetServiceRequirement
from betty.service_level import DownstreamServiceLevel, ServiceLevel
from betty.services.plugin import (
    PluginServiceManager,
    PluginServiceProvider,
    PluginServiceRequirement,
)
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)


class _PluginServiceRequirementTestPluginServiceManager(
    PluginServiceManager[
        PluginServiceProvider,
        DummyPluginDefinition,
        Sequence[DummyPluginDefinition],
        DummyPluginDefinition,
    ]
):
    def __init__(self, *, auto: bool = False):
        super().__init__(DummyPluginDefinition, auto=auto)

    @override
    def new_service(
        self, service_provider: PluginServiceProvider, /
    ) -> Sequence[DummyPluginDefinition]:
        return tuple(
            map(resolve_plugin_definition, self.get_init_plugins(service_provider))
        )


class _PluginServiceRequirementTestServices(ServiceLevel, PluginServiceProvider):
    def __init__(self):
        super().__init__(
            plugins={
                DummyPluginDefinition: (
                    DummyPluginOne,
                    DummyPluginTwo,
                    DummyPluginThree,
                )
            }
        )

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
        async with _PluginServiceRequirementTestServices() as services:
            with pytest.raises(UnmetServiceRequirement):
                await sut(services)

    async def test___call____with_required_service_with_required_plugin(self) -> None:
        sut = PluginServiceRequirement(
            _PluginServiceRequirementTestServices.my_first_plugins, DummyPluginOne
        )
        services = _PluginServiceRequirementTestServices()
        _PluginServiceRequirementTestServices.my_first_plugins.add_init_plugins(
            services, DummyPluginOne.plugin()
        )
        async with services:
            assert DummyPluginOne.plugin() in await sut(services)

    async def test___call____with_upstream_required_service_without_required_plugin(
        self,
    ) -> None:
        sut = PluginServiceRequirement(
            _PluginServiceRequirementTestServices.my_first_plugins, DummyPluginOne
        )
        services = _PluginServiceRequirementTestServices()
        _PluginServiceRequirementTestServices.my_first_plugins.add_init_plugins(
            services, DummyPluginOne.plugin()
        )
        async with _PluginServiceRequirementTestServices() as services:
            with pytest.raises(UnmetServiceRequirement):
                await sut(DownstreamServiceLevel(upstream=services))

    async def test___call____with_upstream_required_service_with_required_plugin(
        self,
    ) -> None:
        sut = PluginServiceRequirement(
            _PluginServiceRequirementTestServices.my_first_plugins, DummyPluginOne
        )
        services = _PluginServiceRequirementTestServices()
        _PluginServiceRequirementTestServices.my_first_plugins.add_init_plugins(
            services, DummyPluginOne.plugin()
        )
        async with services:
            assert DummyPluginOne.plugin() in await sut(
                DownstreamServiceLevel(upstream=services)
            )

    def test_plugins__without_plugins(self) -> None:
        service = _PluginServiceRequirementTestPluginServiceManager()
        sut = PluginServiceRequirement(service)
        assert not sut.plugins

    def test_plugins__with_plugins(self) -> None:
        service = _PluginServiceRequirementTestPluginServiceManager()
        plugins = [DummyPluginOne.plugin(), DummyPluginTwo.plugin()]
        sut = PluginServiceRequirement(service, *plugins)
        assert list(sut.plugins) == plugins

    def test_service(self) -> None:
        service = _PluginServiceRequirementTestPluginServiceManager()
        sut = PluginServiceRequirement(service)
        assert sut.service is service
