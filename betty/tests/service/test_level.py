import pytest

from betty.model import EntityDefinition
from betty.plugin.error import PluginTypeNotFound
from betty.service.level import ServiceLevel
from betty.test_utils.plugin import DummyPluginDefinition


class TestServiceLevel:
    def test_plugins__with_plugin_type_not_found(self) -> None:
        sut = ServiceLevel()
        with pytest.raises(PluginTypeNotFound):
            sut.plugins[DummyPluginDefinition]

    async def test_plugins__with_plugin_definition_cls(self) -> None:
        sut = ServiceLevel()
        assert list(await sut.plugins[EntityDefinition].ids())

    async def test_plugins__with_machine_name(self) -> None:
        sut = ServiceLevel()
        assert list(await sut.plugins[EntityDefinition.type().id].ids())

    async def test_plugins__with_str(self) -> None:
        sut = ServiceLevel()
        assert list(await sut.plugins["entity"].ids())

    async def test_plugins__with_overridden_plugin_type(self) -> None:
        sut = ServiceLevel(plugins={EntityDefinition: []})
        assert not list(await sut.plugins[EntityDefinition].ids())

    async def test_plugins__with_custom_plugin_type(self) -> None:
        sut = ServiceLevel(plugins={DummyPluginDefinition: []})
        assert not list(await sut.plugins[DummyPluginDefinition].ids())

    async def test_factory(self) -> None:
        class _TargetType:
            pass

        sut = ServiceLevel()
        assert isinstance(await sut.factory.new(_TargetType), _TargetType)
