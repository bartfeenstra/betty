from typing_extensions import override

from betty.plugin.config.ordered import OrderedPluginDefinitionConfiguration
from betty.plugin.ordered import OrderedPluginDefinition


class TestOrderedPluginDefinitionConfiguration:
    class _Sut(OrderedPluginDefinitionConfiguration):
        @override
        def new_plugin(self) -> OrderedPluginDefinition:
            raise NotImplementedError

    async def test_comes_before(self) -> None:
        comes_before = ["my-first-plugin"]
        sut = self._Sut(id="-", comes_before=comes_before)
        assert sut.comes_before == comes_before

    async def test_comes_after(self) -> None:
        comes_after = ["my-first-plugin"]
        sut = self._Sut(id="-", comes_after=comes_after)
        assert sut.comes_after == comes_after
