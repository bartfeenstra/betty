from typing import override

from betty.plugin.data.ordered import OrderedPluginDefinitionConfiguration
from betty.plugin.ordered import OrderedPluginDefinition


class TestOrderedPluginDefinitionConfiguration:
    class _Sut(OrderedPluginDefinitionConfiguration):
        @override
        def new_plugin(self) -> OrderedPluginDefinition:
            raise NotImplementedError

    def test_comes_before(self) -> None:
        comes_before = ["my-first-plugin"]
        sut = self._Sut(id="-dummy", comes_before=comes_before)
        assert sut.comes_before == comes_before

    def test_comes_after(self) -> None:
        comes_after = ["my-first-plugin"]
        sut = self._Sut(id="-dummy", comes_after=comes_after)
        assert sut.comes_after == comes_after
