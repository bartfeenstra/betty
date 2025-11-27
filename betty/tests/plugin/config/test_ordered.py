from typing import TYPE_CHECKING

from betty.plugin.config.ordered import OrderedPluginDefinitionConfiguration

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class TestOrderedPluginDefinitionConfiguration:
    async def test_load__minimal(self) -> None:
        dump: Dump = {"id": "hello-world"}
        sut = OrderedPluginDefinitionConfiguration(id="-")
        sut.load(dump)
        assert not sut.comes_before
        assert not sut.comes_after

    async def test_load__with_comes_before(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "comes_before": ["my-first-plugin"],
        }
        sut = OrderedPluginDefinitionConfiguration(id="-")
        sut.load(dump)
        assert sut.comes_before == {"my-first-plugin"}

    async def test_load__with_comes_after(self) -> None:
        dump: Dump = {
            "id": "hello-world",
            "comes_after": ["my-first-plugin"],
        }
        sut = OrderedPluginDefinitionConfiguration(id="-")
        sut.load(dump)
        assert sut.comes_after == {"my-first-plugin"}

    async def test_dump__minimal(self) -> None:
        sut = OrderedPluginDefinitionConfiguration(id="-")
        dump = sut.dump()
        assert "comes_before" not in dump
        assert "comes_after" not in dump

    async def test_dump__with_comes_before(self) -> None:
        comes_before = {"my-first-plugin"}
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_before=comes_before)
        dump = sut.dump()
        assert dump["comes_before"] == list(comes_before)

    async def test_dump__with_comes_after(self) -> None:
        comes_after = {"my-first-plugin"}
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_after=comes_after)
        dump = sut.dump()
        assert dump["comes_after"] == list(comes_after)

    async def test_comes_before(self) -> None:
        comes_before = {"my-first-plugin"}
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_before=comes_before)
        assert sut.comes_before == comes_before

    async def test_comes_after(self) -> None:
        comes_after = {"my-first-plugin"}
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_after=comes_after)
        assert sut.comes_after == comes_after
