from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer
from betty.requirement import (
    RequirableDecorator,
    ServicePluginRequirement,
    UnmetRequirement,
)
from betty.service.level import ChainedServiceLevel, ServiceLevel
from betty.service.plugin.service import (
    ServicePluginDefinition,
    ServicePluginProvider,
    ServicePlugins,
)
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)

if TYPE_CHECKING:
    from collections.abc import Collection


class _ServiceLevel(ServiceLevel):
    pass


class _ChainedServiceLevel(ChainedServiceLevel):
    pass


class _ServicePluginProvider(ServiceLevel, ServicePluginProvider):
    def __init__(
        self,
        service_plugin_types: Collection[type[ServicePluginDefinition]],
        service_plugins: ServicePlugins = (),
        /,
    ):
        super().__init__(
            plugins={_ServicePluginDefinition: [_ServicePluginOne]},
            service_plugin_types=service_plugin_types,
            service_plugins=service_plugins,
            service_plugin_services=self,
        )


class _ChainedServicePluginProvider(ChainedServiceLevel, _ServicePluginProvider):
    def __init__(
        self,
        service_plugin_types: Collection[type[ServicePluginDefinition]],
        service_plugins: ServicePlugins = (),
        *,
        upstream: ServiceLevel,
    ):
        super().__init__(service_plugin_types, service_plugins, upstream=upstream)


class _ServicePlugin(Plugin["_ServicePluginDefinition"]):
    pass


@PluginTypeDefinition(
    "service-plugin",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _ServicePluginDefinition(ServicePluginDefinition[_ServicePlugin]):
    pass


class _ServicePluginManufacturer(
    PluginManufacturer[_ServicePluginDefinition, _ServicePlugin]
):
    @override
    @classmethod
    def plugin_type(cls) -> type[_ServicePluginDefinition]:
        return _ServicePluginDefinition


@_ServicePluginDefinition("service-plugin-one")
class _ServicePluginOne(_ServicePlugin):
    pass


async def _requirement(services: ServiceLevel, /) -> _ServiceLevel:
    if isinstance(services, _ServiceLevel):
        return services
    raise UnmetRequirement("")


class TestServicePluginRequirement:
    def test_plugin(self) -> None:
        assert ServicePluginRequirement(_ServicePluginOne).plugin is _ServicePluginOne

    async def test___call____services_unmet_because_no_service_plugin_provider(
        self,
    ) -> None:
        sut = ServicePluginRequirement(_ServicePluginOne)
        services = _ServiceLevel()
        with pytest.raises(UnmetRequirement):
            await sut(services)

    async def test___call____services_unmet_because_no_service_plugin_type(
        self,
    ) -> None:
        sut = ServicePluginRequirement(_ServicePluginOne)
        async with _ServicePluginProvider({}, []) as services:
            with pytest.raises(UnmetRequirement):
                await sut(services)

    async def test___call____services_unmet_because_no_service_plugin(self) -> None:
        sut = ServicePluginRequirement(_ServicePluginOne)
        async with _ServicePluginProvider({_ServicePluginDefinition}, []) as services:
            with pytest.raises(UnmetRequirement):
                await sut(services)

    async def test___call____services_met(self) -> None:
        sut = ServicePluginRequirement(_ServicePluginOne)
        async with _ServicePluginProvider(
            {_ServicePluginDefinition}, [_ServicePluginOne]
        ) as services:
            assert isinstance(await sut(services), _ServicePluginOne)

    async def test___call____services_unmet_and_upstream_unmet(self) -> None:
        sut = ServicePluginRequirement(_ServicePluginOne)
        services = _ChainedServiceLevel(upstream=_ServiceLevel())
        with pytest.raises(UnmetRequirement):
            await sut(services)

    async def test___call____services_unmet_because_no_service_plugin_provider_but_upstream_met(
        self,
    ) -> None:
        sut = ServicePluginRequirement(_ServicePluginOne)
        async with _ServicePluginProvider(
            {_ServicePluginDefinition}, [_ServicePluginOne]
        ) as upstream:
            services = _ChainedServiceLevel(upstream=upstream)
            assert isinstance(await sut(services), _ServicePluginOne)

    async def test___call____services_unmet_because_no_service_plugin_type_but_upstream_met(
        self,
    ) -> None:
        sut = ServicePluginRequirement(_ServicePluginOne)
        async with (
            _ServicePluginProvider(
                {_ServicePluginDefinition}, [_ServicePluginOne]
            ) as upstream,
            _ChainedServicePluginProvider({}, upstream=upstream) as services,
        ):
            assert isinstance(await sut(services), _ServicePluginOne)

    async def test___call____services_unmet_because_no_service_plugin_but_upstream_met(
        self,
    ) -> None:
        sut = ServicePluginRequirement(_ServicePluginOne)
        async with (
            _ServicePluginProvider(
                {_ServicePluginDefinition}, [_ServicePluginOne]
            ) as upstream,
            _ChainedServicePluginProvider(
                {_ServicePluginDefinition}, [], upstream=upstream
            ) as services,
        ):
            with pytest.raises(UnmetRequirement):
                await sut(services)


class TestRequirableDecorator:
    class _RequirableDecorator(
        RequirableDecorator[tuple[_ServiceLevel, _ServiceLevel]]
    ):
        @override
        async def _check(
            self, services: ServiceLevel, /
        ) -> tuple[_ServiceLevel, _ServiceLevel]:
            if isinstance(services, _ServiceLevel):
                return services, services
            raise UnmetRequirement("uh-oh")

    async def test___call____with_services_and_unmet_requirement(self) -> None:
        with pytest.raises(UnmetRequirement):
            await self._RequirableDecorator()(ServiceLevel())

    async def test___call____with_services_and_met_requirement(self) -> None:
        services = _ServiceLevel()
        assert await self._RequirableDecorator()(services) == (services, services)

    async def test___call____with_decorated_and_unmet_requirement(self) -> None:
        with pytest.raises(UnmetRequirement):
            await self._RequirableDecorator()(lambda services: (services, services))(
                ServiceLevel()
            )

    async def test___call____with_decorated_and_met_requirement(self) -> None:
        services = _ServiceLevel()
        assert await self._RequirableDecorator()(
            lambda services_pair: (services_pair, services_pair)
        )(services) == ((services, services), (services, services))
