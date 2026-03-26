from __future__ import annotations

from collections.abc import Awaitable, Callable, Collection
from typing import override

import pytest

from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer
from betty.requirement import (
    ServiceLevelRequirement,
    ServicePluginRequirement,
    UnmetRequirement,
    require,
    resolve_requirement,
)
from betty.service.level import ChainedServiceLevel, ServiceLevel
from betty.service.plugin import (
    ServicePluginDefinition,
    ServicePluginProvider,
    ServicePlugins,
)
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


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


@require(_requirement)  # ty:ignore[no-matching-overload]
def _require_target_sync(services: _ServiceLevel, /) -> _ServiceLevel:
    return services


@require(_requirement)  # ty:ignore[no-matching-overload]
async def _require_target_async(services: _ServiceLevel, /) -> _ServiceLevel:
    return services


class _RequireTargetClassMethod:
    @classmethod
    @require(_requirement)  # ty:ignore[no-matching-overload]
    async def target(cls, services: _ServiceLevel, /) -> _ServiceLevel:
        return services


class _RequireTargetInstanceMethod:
    @require(_requirement)  # ty:ignore[no-matching-overload]
    async def target(self, services: _ServiceLevel, /) -> _ServiceLevel:
        return services


_targets = pytest.mark.parametrize(
    "target",
    [
        _require_target_sync,
        _require_target_async,
        _RequireTargetClassMethod.target,
        _RequireTargetInstanceMethod().target,
    ],
)
type _Target = Callable[[ServiceLevel], Awaitable[_ServiceLevel]]


class TestRequire:
    async def test___call____with_requirement_unmet(
        self,
    ) -> None:
        def _require_target(services: _ServiceLevel, /) -> _ServiceLevel:
            return services

        sut = require(_requirement)
        with pytest.raises(UnmetRequirement):
            await sut(_require_target)(ServiceLevel())  # ty:ignore[no-matching-overload]

    async def test___call____with_requirement_met(
        self,
    ) -> None:
        def _require_target(services: _ServiceLevel, /) -> _ServiceLevel:
            return services

        sut = require(_requirement)
        services = _ServiceLevel()
        assert await sut(_require_target)(services) is services  # ty:ignore[no-matching-overload]


class TestCallableRequire:
    @_targets
    async def test___call____with_requirement_unmet(self, target: _Target) -> None:
        with pytest.raises(UnmetRequirement):
            await target(ServiceLevel())

    @_targets
    async def test___call____with_requirement_met(self, target: _Target) -> None:
        services = _ServiceLevel()
        assert await target(services) is services


def test_resolve_requirement__with_service_level() -> None:
    actual = resolve_requirement(_ServiceLevel)
    assert isinstance(actual, ServiceLevelRequirement)
    assert actual.services is _ServiceLevel


def test_resolve_requirement__with_service_plugin() -> None:
    actual = resolve_requirement(_ServicePluginOne)
    assert isinstance(actual, ServicePluginRequirement)
    assert actual.plugin is _ServicePluginOne


def test_resolve_requirement__with_requirement() -> None:
    assert resolve_requirement(_requirement) is _requirement


class TestServiceLevelRequirement:
    def test_services(self) -> None:
        assert ServiceLevelRequirement(_ServiceLevel).services is _ServiceLevel

    def test___call____unmet(self) -> None:
        sut = ServiceLevelRequirement(_ServiceLevel)
        with pytest.raises(UnmetRequirement):
            sut(ServiceLevel())

    def test___call____met(self) -> None:
        sut = ServiceLevelRequirement(_ServiceLevel)
        services = _ServiceLevel()
        assert sut(services) is services

    def test___call____chained_unmet(self) -> None:
        sut = ServiceLevelRequirement(_ServiceLevel)
        with pytest.raises(UnmetRequirement):
            sut(_ChainedServiceLevel(upstream=ServiceLevel()))

    def test___call____chained_met(self) -> None:
        sut = ServiceLevelRequirement(_ServiceLevel)
        services = _ServiceLevel()
        assert sut(_ChainedServiceLevel(upstream=services)) is services


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
        async with _ServicePluginProvider({}, [_ServicePluginOne]) as services:
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
