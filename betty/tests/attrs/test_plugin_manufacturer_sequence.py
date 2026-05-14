from betty.attrs.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceAttr,
)
from betty.collection.sequence.adapter import MutableResolvedSequenceAdapter
from betty.property import HasProperties
from betty.test_utils.plugin import DummyPluginManufacturer, DummyPluginOne


class TestPluginManufacturerSequenceAttr:
    class _Owner(HasProperties):
        attr = PluginManufacturerSequenceAttr(DummyPluginManufacturer)

    def test___set__(self) -> None:
        owner = self._Owner()
        owner.attr = DummyPluginOne
        assert isinstance(owner.attr, MutableResolvedSequenceAdapter)
        assert list(owner.attr) == [DummyPluginManufacturer(DummyPluginOne)]
