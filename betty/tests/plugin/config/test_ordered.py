from typing import TYPE_CHECKING

from betty.plugin.config.ordered import OrderedPluginDefinitionConfiguration
from betty.test_utils.config import ConfigurationTestBase

if TYPE_CHECKING:
    from betty.serde import SerializedData


class TestOrderedPluginDefinitionConfiguration(
    ConfigurationTestBase[OrderedPluginDefinitionConfiguration]
):
    sut_cls = OrderedPluginDefinitionConfiguration

    async def test_load__minimal(self) -> None:
        serialized: SerializedData = {"id": "hello-world"}
        sut = OrderedPluginDefinitionConfiguration.load(serialized)
        assert not sut.comes_before
        assert not sut.comes_after

    async def test_load__with_comes_before(self) -> None:
        serialized: SerializedData = {
            "id": "hello-world",
            "comes_before": ["my-first-plugin"],
        }
        sut = OrderedPluginDefinitionConfiguration.load(serialized)
        assert sut.comes_before == {"my-first-plugin"}

    async def test_load__with_comes_after(self) -> None:
        serialized: SerializedData = {
            "id": "hello-world",
            "comes_after": ["my-first-plugin"],
        }
        sut = OrderedPluginDefinitionConfiguration.load(serialized)
        assert sut.comes_after == {"my-first-plugin"}

    async def test_dump__minimal(self) -> None:
        sut = OrderedPluginDefinitionConfiguration(id="-")
        serialized = sut.dump()
        assert "comes_before" not in serialized
        assert "comes_after" not in serialized

    async def test_dump__with_comes_before(self) -> None:
        comes_before = {"my-first-plugin"}
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_before=comes_before)
        serialized = sut.dump()
        assert serialized["comes_before"] == list(comes_before)

    async def test_dump__with_comes_after(self) -> None:
        comes_after = {"my-first-plugin"}
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_after=comes_after)
        serialized = sut.dump()
        assert serialized["comes_after"] == list(comes_after)

    async def test_comes_before(self) -> None:
        comes_before = {"my-first-plugin"}
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_before=comes_before)
        assert sut.comes_before == comes_before

    async def test_comes_after(self) -> None:
        comes_after = {"my-first-plugin"}
        sut = OrderedPluginDefinitionConfiguration(id="-", comes_after=comes_after)
        assert sut.comes_after == comes_after
