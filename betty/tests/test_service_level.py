from __future__ import annotations

import pytest

from betty.plugin.error import PluginTypeNotFound
from betty.service_level import (
    DownstreamServiceLevel,
    HasServiceLevel,
    ServiceLevel,
    resolve_service_level,
)
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne


class TestServiceLevel:
    def test_plugins__with_plugin_type_not_found(self) -> None:
        sut = ServiceLevel()
        with pytest.raises(PluginTypeNotFound):
            sut.plugins[DummyPluginDefinition]

    async def test_plugins__with_plugin_definition_cls(self) -> None:
        sut = ServiceLevel(plugins={DummyPluginDefinition: [DummyPluginOne]})
        assert list(await sut.plugins[DummyPluginDefinition].ids())

    async def test_plugins__with_machine_name(self) -> None:
        sut = ServiceLevel(plugins={DummyPluginDefinition: [DummyPluginOne]})
        assert list(await sut.plugins[DummyPluginDefinition.type().id].ids())

    async def test_plugins__with_str(self) -> None:
        sut = ServiceLevel(plugins={DummyPluginDefinition: [DummyPluginOne]})
        assert list(await sut.plugins[str(DummyPluginDefinition.type().id)].ids())

    async def test_factory(self) -> None:
        class _TargetType:
            pass

        sut = ServiceLevel()
        assert isinstance(await sut.factory.new(_TargetType), _TargetType)


class TestDownstreamServiceLevel:
    def test_upstream(self) -> None:
        upstream = ServiceLevel()
        sut = DownstreamServiceLevel(upstream=upstream)
        assert sut.upstream is upstream


class TestHasServiceLevel:
    def test___init__(self) -> None:
        class _Owner(HasServiceLevel):
            pass

        services = ServiceLevel()
        owner = _Owner(services=services)
        assert owner.services is services


def test_resolve_service_level__with_service_level() -> None:
    services = ServiceLevel()
    assert resolve_service_level(services) is services


def test_resolve_service_level__with_has_service_level() -> None:
    services = ServiceLevel()
    assert resolve_service_level(HasServiceLevel(services=services)) is services
