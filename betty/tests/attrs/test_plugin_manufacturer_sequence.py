from betty.attrs.plugin_manufacturer_sequence import (
    new_plugin_manufacturer_sequence_attr,
)
from betty.collections.sequence.adapter import MutableResolvedSequenceAdapter
from betty.prop import HasProps
from betty.test_utils.plugin import DummyPluginManufacturer, DummyPluginOne


class _Owner(HasProps):
    attr = new_plugin_manufacturer_sequence_attr(DummyPluginManufacturer)


def test_new_plugin_manufacturer_sequence_attr__set() -> None:
    owner = _Owner()
    owner.attr = DummyPluginOne
    assert isinstance(owner.attr, MutableResolvedSequenceAdapter)
    assert list(owner.attr) == [DummyPluginManufacturer(DummyPluginOne)]
