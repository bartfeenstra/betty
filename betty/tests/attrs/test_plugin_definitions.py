from collections.abc import Iterable
from typing import override

from betty.attrs.plugin_definitions import new_plugin_definition_datas_attr
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.plugin.definition import (
    PluginDefinitionData,
    PluginDefinitionDefinition,
)
from betty.definition.human_facing import HumanFacingDefinition
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.prop import HasProps
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


@ObjectDefinition(label="-")
class _Owner(Data, HasProps):
    @PluginDefinitionDefinition(_DummyPluginDefinition)
    class _Item(PluginDefinitionData[_DummyPluginDefinition]):
        @override
        def new_plugin(self) -> _DummyPluginDefinition:
            raise Unreachable

    def __init__(self, plugins: Iterable[_Item] = ()):
        super().__init__()
        self.plugins = plugins

    plugins = new_plugin_definition_datas_attr(_DummyPluginDefinition, _Item)


def test_new_plugin_definition_datas_attr__key() -> None:
    plugin_id = "my-first-plugin"
    item = _Owner._Item(id=plugin_id)
    owner = _Owner()
    owner.plugins.add(item)
    assert owner.plugins[plugin_id] is item


def test_new_plugin_definition_datas_attr__load_minimal() -> None:
    _Owner.data().porter.load({})


def test_new_plugin_definition_datas_attr__load() -> None:
    plugin_id = "my-first-plugin"
    owner = _Owner.data().porter.load({"plugins": {plugin_id: {}}})
    assert owner.plugins[plugin_id].id == plugin_id


def test_new_plugin_definition_datas_attr__dump_minimal() -> None:
    assert _Owner.data().porter.dump(_Owner()) == {}


def test_new_plugin_definition_datas_attr__dump() -> None:
    plugin_id = "my-first-plugin"
    item = _Owner._Item(id=plugin_id)
    assert _Owner.data().porter.dump(_Owner([item])) == {"plugins": {plugin_id: {}}}
