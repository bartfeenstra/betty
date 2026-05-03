from betty.collection.sequence.adapter import MutableResolvedSequenceAdapter
from betty.properties.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceProperty,
)
from betty.test_utils.plugin import DummyPluginManufacturer, DummyPluginOne


class TestPluginManufacturerSequenceProperty:
    class _Instance:
        attr = PluginManufacturerSequenceProperty(DummyPluginManufacturer)

    def test___set__(self) -> None:
        instance = self._Instance()
        instance.attr = DummyPluginOne
        assert isinstance(instance.attr, MutableResolvedSequenceAdapter)
        assert list(instance.attr) == [DummyPluginManufacturer(DummyPluginOne)]
