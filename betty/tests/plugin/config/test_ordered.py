from betty.plugin.config.ordered import OrderedPluginDefinitionConfiguration


class TestOrderedPluginDefinitionConfiguration:
    async def test_comes_before(self) -> None:
        comes_before = ["my-first-plugin"]
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_before=comes_before)
        assert sut.comes_before == comes_before

    async def test_comes_after(self) -> None:
        comes_after = ["my-first-plugin"]
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_after=comes_after)
        assert sut.comes_after == comes_after
