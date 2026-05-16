from collections.abc import Iterable
from typing import override

from betty.attrs.plugin_definitions import PluginDefinitionDatasAttr
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.plugin_definition import PluginDefinitionData
from betty.property import HasProperties
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.plugin import DummyPluginDefinition


class TestPluginDefinitionDatasAttr:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data, HasProperties):
        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Item(PluginDefinitionData[DummyPluginDefinition]):
            @override
            def new_plugin(self) -> DummyPluginDefinition:
                raise NotImplementedError

        def __init__(self, plugins: Iterable[_Item] = ()):
            super().__init__()
            self.plugins = plugins

        plugins = PluginDefinitionDatasAttr(DummyPluginDefinition, _Item)

    def test_key(self) -> None:
        plugin_id = "my-first-plugin"
        item = self._Owner._Item(id=plugin_id)
        owner = self._Owner()
        owner.plugins.add(item)
        assert owner.plugins[plugin_id] is item

    def test_load__minimal(self) -> None:
        self._Owner.data().porter.load({})

    def test_load(self) -> None:
        plugin_id = "my-first-plugin"
        owner = self._Owner.data().porter.load({"plugins": {plugin_id: {}}})
        assert owner.plugins[plugin_id].id == plugin_id

    def test_dump__minimal(self) -> None:
        assert self._Owner.data().porter.dump(self._Owner()) == {}

    def test_dump(self) -> None:
        plugin_id = "my-first-plugin"
        item = self._Owner._Item(id=plugin_id)
        assert self._Owner.data().porter.dump(self._Owner([item])) == {
            "plugins": {plugin_id: {}}
        }
