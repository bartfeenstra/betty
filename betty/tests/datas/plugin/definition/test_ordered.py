from typing import override

from betty.datas.plugin.definition.ordered import OrderedPluginDefinitionData
from betty.plugin.ordered import OrderedPluginDefinition


class TestOrderedPluginDefinitionData:
    class _Sut(OrderedPluginDefinitionData):
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
