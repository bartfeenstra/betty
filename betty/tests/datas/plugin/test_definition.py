from typing import override

from betty.datas.plugin.definition import (
    PluginDefinitionData,
    PluginDefinitionDefinition,
)
from betty.definition.human_facing import HumanFacingDefinition
from betty.localizer import default_localizer
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.portable import KeyedPorter
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE
from betty.typing import Unreachable


@PluginTypeDefinition(
    "dummy-plugin",
    label="dummy plugin",
    label_plural="dummy plugin",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _DummyPluginDefinition(PluginDefinition, HumanFacingDefinition):
    pass


@PluginDefinitionDefinition(_DummyPluginDefinition)
class _DummyPluginDefinitionData(PluginDefinitionData[_DummyPluginDefinition]):
    @override
    def new_plugin(self) -> _DummyPluginDefinition:
        raise Unreachable


class TestPluginDefinitionData:
    def test_id(self) -> None:
        plugin_id = "hello-world"
        sut = _DummyPluginDefinitionData(id=plugin_id)
        assert sut.id == plugin_id


class TestPluginDefinitionDefinition:
    def test_label(self) -> None:
        assert PluginDefinitionDefinition(_DummyPluginDefinition).label.localize(
            default_localizer
        )

    def test_porter__dump(self) -> None:
        assert _DummyPluginDefinitionData.data().porter.dump(
            _DummyPluginDefinitionData(id="hello-world")
        ) == {"id": "hello-world"}

    def test_porter__dump_keyed(self) -> None:
        porter = _DummyPluginDefinitionData.data().porter
        assert isinstance(porter, KeyedPorter)
        assert porter.dump_keyed(_DummyPluginDefinitionData(id="hello-world")) == (
            "hello-world",
            {},
        )

    def test_porter__load(self) -> None:
        assert _DummyPluginDefinitionData.data().porter.load({
            "id": "hello-world"
        }) == _DummyPluginDefinitionData(id="hello-world")

    def test_porter__load_keyed(self) -> None:
        porter = _DummyPluginDefinitionData.data().porter
        assert isinstance(porter, KeyedPorter)
        assert porter.load_keyed("hello-world", {}) == _DummyPluginDefinitionData(
            id="hello-world"
        )
