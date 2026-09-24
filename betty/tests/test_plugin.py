from __future__ import annotations

from typing import TYPE_CHECKING

from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE
from betty.typing import Unreachable

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel


class TestPluginTypeDefinition:
    def test_id(self) -> None:
        plugin_type_id = "my-first-plugin-type"
        sut = PluginTypeDefinition(
            plugin_type_id,
            label="-",
            label_plural="-",
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.id == plugin_type_id


class TestPluginDefinition:
    def test_id(self) -> None:
        id = "my-first-plugin"  # noqa: A001
        sut = PluginDefinition(id)
        assert sut.id == id

    def test_requires(self) -> None:
        def requirement(services: ServiceLevel, /) -> None:
            raise Unreachable

        requires = list(
            PluginDefinition("my-first-plugin-id", requires={requirement}).requires
        )
        assert len(requires) == 1
        assert requires[0] is requirement

    def test_auto(self) -> None:
        assert PluginDefinition("my-first-plugin-id", auto=True).auto
        assert not PluginDefinition("my-first-plugin-id", auto=False).auto
