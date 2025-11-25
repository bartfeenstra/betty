from __future__ import annotations

from betty.locale.localizable import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginDefinition, PluginTypeDefinition, plugin_types
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.discovery import discover
from betty.plugin.discovery.static import StaticDiscovery
from betty.plugin.ordered import OrderedPluginDefinition
from betty.test_utils.plugin import DummyPluginOne, DummyPluginTwo


class _OrderedPluginDefinition(OrderedPluginDefinition):
    type = PluginTypeDefinition(
        id="ordered-plugin",
        label="",
    )


_ORDERED_PLUGIN_COMES_BEFORE_TARGET = _OrderedPluginDefinition(
    id="ordered-plugin-comes-before-target",
)

_ORDERED_PLUGIN_HAS_COMES_BEFORE = _OrderedPluginDefinition(
    id="ordered-plugin-has-comes-before",
    comes_before={_ORDERED_PLUGIN_COMES_BEFORE_TARGET},
)
_ORDERED_PLUGIN_COMES_AFTER_TARGET = _OrderedPluginDefinition(
    id="ordered-plugin-comes-after-target",
)

_ORDERED_PLUGIN_HAS_COMES_AFTER = _OrderedPluginDefinition(
    id="ordered-plugin-has-comes-after",
    comes_after={_ORDERED_PLUGIN_COMES_AFTER_TARGET},
)

_ORDERED_PLUGIN_ISOLATED = _OrderedPluginDefinition(
    id="ordered-plugin-isolated",
)


_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL = _OrderedPluginDefinition(
    id="ordered-plugin-has-comes-before-bidirectional",
    comes_before={"ordered-plugin-has-comes-after-bidirectional"},
)
_ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL = _OrderedPluginDefinition(
    id="ordered-plugin-has-comes-after-bidirectional",
    comes_after={_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL},
)


class _DependentPluginDefinition(DependentPluginDefinition):
    type = PluginTypeDefinition(
        id="dependent",
        label="_ExpandPluginDependenciesTestPluginDefinition",
    )


_DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT = _DependentPluginDefinition(
    id="expand-plugin-dependencies-test-downstream-dependent",
)
_DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT = _DependentPluginDefinition(
    id="expand-plugin-dependencies-test-upstream-and-downstream-dependent",
    depends_on={_DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT},
)
_DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT = _DependentPluginDefinition(
    id="expand-plugin-dependencies-test-upstream-dependent",
    depends_on={_DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT},
)

_DEPENDENT_PLUGIN_ISOLATED = _DependentPluginDefinition(
    id="expand-plugin-dependencies-test-isolated",
)


class TestPluginTypeDefinition:
    def test_id(self) -> None:
        plugin_type_id = "my-first-plugin-type"
        sut = PluginTypeDefinition(
            id=plugin_type_id,
            label="",
        )
        assert sut.id == plugin_type_id

    def test_label(self) -> None:
        label = Plain("my-first-plugin-type")
        sut = PluginTypeDefinition(
            label=label,
            id="my-first-plugin-type",
        )
        assert sut.label is label

    def test_discoveries(self) -> None:
        discovery = StaticDiscovery()
        sut = PluginTypeDefinition(
            label="my-first-plugin-type",
            id="my-first-plugin-type",
            discoveries=discovery,
        )
        assert discovery in sut.discoveries

    def test_add_discovery(self) -> None:
        discovery = StaticDiscovery()
        sut = PluginTypeDefinition(
            label="my-first-plugin-type",
            id="my-first-plugin-type",
        )
        sut.add_discovery(discovery)
        assert discovery in sut.discoveries

    def test_override_discovery(self) -> None:
        sut = PluginTypeDefinition(
            label="my-first-plugin-type",
            id="my-first-plugin-type",
        )
        assert not sut.discoveries
        with sut.override_discovery(DummyPluginOne):
            assert sut.discoveries
        assert not sut.discoveries

    async def test_add_discovery__during_override_discovery(self) -> None:
        sut = PluginTypeDefinition(
            label="my-first-plugin-type",
            id="my-first-plugin-type",
        )
        with sut.override_discovery(DummyPluginOne):
            sut.add_discovery(StaticDiscovery(DummyPluginTwo))
            assert DummyPluginTwo not in await discover(None, *sut.discoveries)
        assert DummyPluginOne not in await discover(None, *sut.discoveries)
        assert DummyPluginTwo in await discover(None, *sut.discoveries)

    def test_discovery_overridden(self) -> None:
        sut = PluginTypeDefinition(
            label="my-first-plugin-type",
            id="my-first-plugin-type",
        )
        assert not sut.discovery_overridden
        with sut.override_discovery():
            assert sut.discovery_overridden
        assert not sut.discovery_overridden  # type: ignore[unreachable]


class TestPluginDefinition:
    def test_id(self) -> None:
        id = "my-first-plugin"  # noqa A001
        sut = PluginDefinition(id=id)
        assert sut.id == id

    def test_reference_label(self) -> None:
        id = "my-first-plugin"  # noqa A001
        sut = PluginDefinition(id=id)
        actual = sut.reference_label.localize(DEFAULT_LOCALIZER)
        assert id in actual

    def test_reference_label_with_type(self) -> None:
        plugin_type_label = "My First Plugin Type"

        class _PluginDefinition(PluginDefinition):
            type = PluginTypeDefinition(
                id="my-first-plugin-type", label=plugin_type_label
            )

        id = "my-first-plugin"  # noqa A001
        sut = _PluginDefinition(id=id)
        actual = sut.reference_label_with_type.localize(DEFAULT_LOCALIZER)
        assert id in actual
        assert plugin_type_label in actual


def test_plugin_types() -> None:
    assert plugin_types()
