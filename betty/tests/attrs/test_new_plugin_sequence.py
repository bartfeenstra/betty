from betty.attrs.new_plugin_sequence import (
    new_new_plugin_sequence_attr,
)
from betty.collections.sequence.adapter import MutableResolvedSequenceAdapter
from betty.prop import HasProps
from betty.test_utils.plugin import DummyPluginOne, NewDummyPlugin


class _Owner(HasProps):
    attr = new_new_plugin_sequence_attr(NewDummyPlugin)


def test_new_new_plugin_sequence_attr__set() -> None:
    owner = _Owner()
    owner.attr = [DummyPluginOne]
    assert isinstance(owner.attr, MutableResolvedSequenceAdapter)
    assert list(owner.attr) == [NewDummyPlugin(DummyPluginOne)]
