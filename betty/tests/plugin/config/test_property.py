from collections.abc import Iterable

from typing_extensions import override

from betty.collections import MutableResolvedSequenceProxy
from betty.data import Data
from betty.data.aggregate.record.object import ObjectDefinition
from betty.plugin.config import (
    PluginConfiguration,
    PluginDefinitionConfiguration,
)
from betty.plugin.config.property import (
    PluginConfigurationSequenceProperty,
    PluginDefinitionConfigurationsProperty,
)
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne


class TestPluginConfigurationSequenceProperty:
    class _Instance:
        attr = PluginConfigurationSequenceProperty(DummyPluginDefinition)

    def test___set__(self) -> None:
        instance = self._Instance()
        instance.attr = DummyPluginOne
        assert isinstance(instance.attr, MutableResolvedSequenceProxy)
        assert list(instance.attr) == [PluginConfiguration(DummyPluginOne)]


class TestPluginDefinitionConfigurationsProperty:
    @ObjectDefinition(label=DUMMY_LOCALIZABLE)
    class _Owner(Data):
        @ObjectDefinition(label=DUMMY_LOCALIZABLE)
        class _Item(PluginDefinitionConfiguration[DummyPluginDefinition]):
            @override
            def new_plugin(self) -> DummyPluginDefinition:
                raise NotImplementedError

        def __init__(self, plugins: Iterable[_Item] | None = None):
            if plugins is not None:
                self.plugins = plugins

        plugins = PluginDefinitionConfigurationsProperty(DummyPluginDefinition, _Item)

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
        assert owner.plugin[plugin_id].id == plugin_id

    def test_dump__minimal(self) -> None:
        assert self._Owner.data().porter.dump(self._Owner()) == {}

    def test_dump(self) -> None:
        plugin_id = "my-first-plugin"
        item = self._Owner._Item(id=plugin_id)
        assert self._Owner.data().porter.dump(self._Owner([item])) == {
            "plugins": {plugin_id: {}}
        }
