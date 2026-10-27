from typing import override

from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.plugin.definition import (
    PluginDefinitionConfig,
    PluginDefinitionConfigDefinition,
)
from betty.localizer import default_localizer
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.portable import KeyedPorter
from betty.test_utils.locale.localizable import dummy_countable_localizable
from betty.typing import Unreachable


@PluginTypeDefinition(
    "dummy-plugin",
    label="dummy plugin",
    label_plural="dummy plugin",
    label_countable=dummy_countable_localizable,
)
class _DummyPluginDefinition(PluginDefinition, ObjectDefinition):
    pass


@PluginDefinitionConfigDefinition(_DummyPluginDefinition)
class _DummyPluginDefinitionConfig(PluginDefinitionConfig[_DummyPluginDefinition]):
    @override
    def new_definition(self) -> _DummyPluginDefinition:
        raise Unreachable


class TestPluginDefinitionConfigDefinition:
    def test_label(self) -> None:
        assert default_localizer.localize(
            PluginDefinitionConfigDefinition(_DummyPluginDefinition).label
        )

    def test_porter__dump(self) -> None:
        assert _DummyPluginDefinitionConfig.definition.porter.dump(
            _DummyPluginDefinitionConfig(id="hello-world")
        ) == {"id": "hello-world"}

    def test_porter__dump_keyed(self) -> None:
        porter = _DummyPluginDefinitionConfig.definition.porter
        assert isinstance(porter, KeyedPorter)
        assert porter.dump_keyed(_DummyPluginDefinitionConfig(id="hello-world")) == (
            "hello-world",
            {},
        )

    def test_porter__load(self) -> None:
        assert _DummyPluginDefinitionConfig.definition.porter.load({
            "id": "hello-world"
        }) == _DummyPluginDefinitionConfig(id="hello-world")

    def test_porter__load_keyed(self) -> None:
        porter = _DummyPluginDefinitionConfig.definition.porter
        assert isinstance(porter, KeyedPorter)
        assert porter.load_keyed("hello-world", {}) == _DummyPluginDefinitionConfig(
            id="hello-world"
        )
