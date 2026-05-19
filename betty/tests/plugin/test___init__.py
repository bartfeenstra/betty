from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.ordered import OrderedPluginClsDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)
from betty.test_utils.plugin import DummyPlugin

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel


@final
@PluginTypeDefinition(
    "ordered-plugin",
    label="_OrderedPluginDefinition",
    label_plural="_OrderedPluginDefinitions",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _OrderedPluginDefinition(OrderedPluginClsDefinition[DummyPlugin]):
    pass


_ORDERED_PLUGIN_COMES_BEFORE_TARGET = _OrderedPluginDefinition(
    "ordered-plugin-comes-before-target"
)

_ORDERED_PLUGIN_HAS_COMES_BEFORE = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-before",
    before={_ORDERED_PLUGIN_COMES_BEFORE_TARGET},
)
_ORDERED_PLUGIN_COMES_AFTER_TARGET = _OrderedPluginDefinition(
    "ordered-plugin-comes-after-target"
)

_ORDERED_PLUGIN_HAS_COMES_AFTER = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-after", after={_ORDERED_PLUGIN_COMES_AFTER_TARGET}
)

_ORDERED_PLUGIN_ISOLATED = _OrderedPluginDefinition("ordered-plugin-isolated")


_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-before-bidirectional",
    before={"ordered-plugin-has-comes-after-bidirectional"},
)
_ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-after-bidirectional",
    after={_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL},
)


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
            raise NotImplementedError

        requires = list(
            PluginDefinition("my-first-plugin-id", requires={requirement}).requires
        )
        assert len(requires) == 1
        assert requires[0] is requirement

    def test_auto(self) -> None:
        assert PluginDefinition("my-first-plugin-id", auto=True).auto
        assert not PluginDefinition("my-first-plugin-id", auto=False).auto
