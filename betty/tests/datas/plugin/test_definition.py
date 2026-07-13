from typing import override

from betty.datas.plugin.definition import (
    PluginDefinitionData,
    PluginDefinitionDefinition,
)
from betty.localizer import default_localizer
from betty.test_utils.plugin import DummyPluginDefinition


@PluginDefinitionDefinition(DummyPluginDefinition)
class _DummyPluginDefinitionData(PluginDefinitionData[DummyPluginDefinition]):
    @override
    def new_plugin(self) -> DummyPluginDefinition:
        raise NotImplementedError


class TestPluginDefinitionData:
    def test_id(self) -> None:
        plugin_id = "hello-world"
        sut = _DummyPluginDefinitionData(id=plugin_id)
        assert sut.id == plugin_id


class TestPluginDefinitionDefinition:
    def test_label(self) -> None:
        assert PluginDefinitionDefinition(DummyPluginDefinition).label.localize(
            default_localizer
        )

    def test_porter__dump(self) -> None:
        assert _DummyPluginDefinitionData.data().porter.dump(
            _DummyPluginDefinitionData(id="hello-world")
        ) == {"id": "hello-world"}

    def test_porter__dump_keyed(self) -> None:
        assert _DummyPluginDefinitionData.data().porter.dump_keyed(
            _DummyPluginDefinitionData(id="hello-world")
        ) == ("hello-world", {})

    def test_porter__load(self) -> None:
        assert _DummyPluginDefinitionData.data().porter.load({
            "id": "hello-world"
        }) == _DummyPluginDefinitionData(id="hello-world")

    def test_porter__load_keyed(self) -> None:
        assert _DummyPluginDefinitionData.data().porter.load_keyed(
            "hello-world", {}
        ) == _DummyPluginDefinitionData(id="hello-world")
