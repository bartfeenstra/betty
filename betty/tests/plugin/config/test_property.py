from betty.collections import ResolvingMutableSequence
from betty.plugin.config import PluginConfiguration
from betty.plugin.config.property import PluginConfigurationSequenceProperty
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne


class TestPluginConfigurationSequenceProperty:
    class _Instance:
        attr = PluginConfigurationSequenceProperty(DummyPluginDefinition)

    def test___set__(self) -> None:
        instance = self._Instance()
        instance.attr = DummyPluginOne
        assert isinstance(instance.attr, ResolvingMutableSequence)
        assert list(instance.attr) == [PluginConfiguration(DummyPluginOne)]
