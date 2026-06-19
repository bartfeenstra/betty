from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

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


_ordered_plugin_comes_before_target: Final[OrderedPluginClsDefinition] = (
    _OrderedPluginDefinition("ordered-plugin-comes-before-target")
)

_ordered_plugin_has_comes_before: Final[OrderedPluginClsDefinition] = (
    _OrderedPluginDefinition(
        "ordered-plugin-has-comes-before",
        before={_ordered_plugin_comes_before_target},
    )
)
_ordered_plugin_comes_after_target: Final[OrderedPluginClsDefinition] = (
    _OrderedPluginDefinition("ordered-plugin-comes-after-target")
)

_ordered_plugin_has_comes_after: Final[OrderedPluginClsDefinition] = (
    _OrderedPluginDefinition(
        "ordered-plugin-has-comes-after", after={_ordered_plugin_comes_after_target}
    )
)

_ordered_plugin_isolated: Final[OrderedPluginClsDefinition] = _OrderedPluginDefinition(
    "ordered-plugin-isolated"
)


_ordered_plugin_has_comes_before_bidirectional: Final[OrderedPluginClsDefinition] = (
    _OrderedPluginDefinition(
        "ordered-plugin-has-comes-before-bidirectional",
        before={"ordered-plugin-has-comes-after-bidirectional"},
    )
)

_ordered_plugin_has_comes_after_bidirectional: Final[OrderedPluginClsDefinition] = (
    _OrderedPluginDefinition(
        "ordered-plugin-has-comes-after-bidirectional",
        after={_ordered_plugin_has_comes_before_bidirectional},
    )
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
