from typing import override

from betty.datas.plugin_definition import PluginDefinitionData
from betty.test_utils.plugin import DummyPluginDefinition


class _DummyPluginDefinitionData(PluginDefinitionData[DummyPluginDefinition]):
    @override
    def new_plugin(self) -> DummyPluginDefinition:
        raise NotImplementedError


class TestPluginDefinitionData:
    def test_id(self) -> None:
        plugin_id = "hello-world"
        sut = _DummyPluginDefinitionData(id=plugin_id)
        assert sut.id == plugin_id
