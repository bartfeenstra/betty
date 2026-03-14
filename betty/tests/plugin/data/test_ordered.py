from typing import override

from betty.plugin.data.ordered import OrderedPluginDefinitionConfiguration
from betty.plugin.ordered import OrderedPluginDefinition


class TestOrderedPluginDefinitionConfiguration:
    class _Sut(OrderedPluginDefinitionConfiguration):
        @override
        def new_plugin(self) -> OrderedPluginDefinition:
            raise NotImplementedError

    def test_before(self) -> None:
        before = ["my-first-plugin"]
        sut = self._Sut(id="-dummy", before=before)
        assert sut.before == before

    def test_after(self) -> None:
        after = ["my-first-plugin"]
        sut = self._Sut(id="-dummy", after=after)
        assert sut.after == after
