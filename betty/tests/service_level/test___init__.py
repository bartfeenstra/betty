import pytest

from betty.plugin.error import PluginTypeNotFound
from betty.service_level import DownstreamServiceLevel, ServiceLevel
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
