from betty.attrs.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceAttr,
)
from betty.collection.sequence.adapter import MutableResolvedSequenceAdapter
from betty.test_utils.plugin import DummyPluginManufacturer, DummyPluginOne


class TestPluginManufacturerSequenceAttr:
    class _Instance:
        attr = PluginManufacturerSequenceAttr(DummyPluginManufacturer)

    def test___set__(self) -> None:
        instance = self._Instance()
        instance.attr = DummyPluginOne
        assert isinstance(instance.attr, MutableResolvedSequenceAdapter)
        assert list(instance.attr) == [DummyPluginManufacturer(DummyPluginOne)]
