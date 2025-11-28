from __future__ import annotations

import pytest

from betty.locale.localizable import CountablePlain, Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition, plugin_types
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.discovery import discover
from betty.plugin.discovery.static import StaticDiscovery
from betty.plugin.ordered import OrderedPluginDefinition
from betty.test_utils.plugin import DummyPluginOne, DummyPluginTwo


class _OrderedPluginDefinition(OrderedPluginDefinition):
    type = PluginTypeDefinition(
        "ordered-plugin",
        "_OrderedPluginDefinition",
        "_OrderedPluginDefinitions",
        CountablePlain(
            "{count} _OrderedPluginDefinition", "{count} _OrderedPluginDefinitions"
        ),
    )


_ORDERED_PLUGIN_COMES_BEFORE_TARGET = _OrderedPluginDefinition(
    "ordered-plugin-comes-before-target"
)

_ORDERED_PLUGIN_HAS_COMES_BEFORE = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-before",
    comes_before={_ORDERED_PLUGIN_COMES_BEFORE_TARGET},
)
_ORDERED_PLUGIN_COMES_AFTER_TARGET = _OrderedPluginDefinition(
    "ordered-plugin-comes-after-target"
)

_ORDERED_PLUGIN_HAS_COMES_AFTER = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-after", comes_after={_ORDERED_PLUGIN_COMES_AFTER_TARGET}
)

_ORDERED_PLUGIN_ISOLATED = _OrderedPluginDefinition("ordered-plugin-isolated")


_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-before-bidirectional",
    comes_before={"ordered-plugin-has-comes-after-bidirectional"},
)
_ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-after-bidirectional",
    comes_after={_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL},
)


class _DependentPluginDefinition(DependentPluginDefinition):
    type = PluginTypeDefinition(
        "dependent",
        "_DependentPluginDefinition",
        "_DependentPluginDefinition",
        CountablePlain(
            "{count} _DependentPluginDefinition", "{count} _DependentPluginDefinitions"
        ),
    )


_DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT = _DependentPluginDefinition(
    "expand-plugin-dependencies-test-downstream-dependent"
)
_DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT = _DependentPluginDefinition(
    "expand-plugin-dependencies-test-upstream-and-downstream-dependent",
    depends_on={_DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT},
)
_DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT = _DependentPluginDefinition(
    "expand-plugin-dependencies-test-upstream-dependent",
    depends_on={_DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT},
)

_DEPENDENT_PLUGIN_ISOLATED = _DependentPluginDefinition(
    "expand-plugin-dependencies-test-isolated"
)


class TestPluginTypeDefinition:
    def test_id(self) -> None:
        plugin_type_id = "my-first-plugin-type"
        sut = PluginTypeDefinition(plugin_type_id, "", "", CountablePlain("", ""))
        assert sut.id == plugin_type_id

    def test_label(self) -> None:
        label = Plain("")
        sut = PluginTypeDefinition("-", label, "", CountablePlain("", ""))
        assert sut.label is label

    def test_label_plural(self) -> None:
        label_plural = Plain("")
        sut = PluginTypeDefinition("-", "", label_plural, CountablePlain("", ""))
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = CountablePlain("", "")
        sut = PluginTypeDefinition("-", "", "", label_countable)
        assert sut.label_countable is label_countable

    def test_description(self) -> None:
        description = Plain("")
        sut = PluginTypeDefinition(
            "-", "", "", CountablePlain("", ""), description=description
        )
        assert sut.description is description

    def test_discoveries(self) -> None:
        discovery = StaticDiscovery()
        sut = PluginTypeDefinition(
            "-", "", "", CountablePlain("", ""), discoveries=discovery
        )
        assert discovery in sut.discoveries

    def test_add_discovery(self) -> None:
        discovery = StaticDiscovery()
        sut = PluginTypeDefinition("-", "", "", CountablePlain("", ""))
        sut.add_discovery(discovery)
        assert discovery in sut.discoveries

    def test_override_discovery(self) -> None:
        sut = PluginTypeDefinition("-", "", "", CountablePlain("", ""))
        assert not sut.discoveries
        with sut.override_discovery(DummyPluginOne.plugin):
            assert sut.discoveries
        assert not sut.discoveries

    async def test_add_discovery__during_override_discovery(self) -> None:
        sut = PluginTypeDefinition("-", "", "", CountablePlain("", ""))
        with sut.override_discovery(DummyPluginOne.plugin):
            sut.add_discovery(StaticDiscovery(DummyPluginTwo.plugin))
            assert DummyPluginTwo.plugin not in await discover(None, *sut.discoveries)
        assert DummyPluginOne.plugin not in await discover(None, *sut.discoveries)
        assert DummyPluginTwo.plugin in await discover(None, *sut.discoveries)

    def test_discovery_overridden(self) -> None:
        sut = PluginTypeDefinition("-", "", "", CountablePlain("", ""))
        assert not sut.discovery_overridden
        with sut.override_discovery():
            assert sut.discovery_overridden
        assert not sut.discovery_overridden  # type: ignore[unreachable]


class TestPluginDefinition:
    def test_id(self) -> None:
        id = "my-first-plugin"  # noqa A001
        sut = PluginDefinition(id)
        assert sut.id == id

    def test_cls(self) -> None:
        sut = PluginDefinition("my-first-plugin")
        with pytest.raises(ValueError):  # noqa PT011
            sut.cls  # noqa B018

    def test___call__(self) -> None:
        class _Plugin(Plugin):
            pass

        sut = PluginDefinition("my-first-plugin")
        cls = sut(_Plugin)
        assert sut.cls is cls
        with pytest.raises(ValueError):  # noqa PT011
            sut(_Plugin)

    def test_reference_label(self) -> None:
        id = "my-first-plugin"  # noqa A001
        sut = PluginDefinition(id)
        actual = sut.reference_label.localize(DEFAULT_LOCALIZER)
        assert id in actual

    def test_reference_label_with_type(self) -> None:
        plugin_type_label = "My First Plugin Type"

        class _PluginDefinition(PluginDefinition):
            type = PluginTypeDefinition(
                "my-first-plugin-type",
                plugin_type_label,
                Plain(""),
                CountablePlain("", ""),
            )

        id = "my-first-plugin"  # noqa A001
        sut = _PluginDefinition(id)
        actual = sut.reference_label_with_type.localize(DEFAULT_LOCALIZER)
        assert id in actual
        assert plugin_type_label in actual


def test_plugin_types() -> None:
    assert plugin_types()
