from __future__ import annotations

import pytest

from betty.locale.localize import DEFAULT_LOCALIZER
from betty.model import EntityDefinition
from betty.plugin import (
    Plugin,
    PluginDefinition,
    PluginTypeDefinition,
    PluginTypeRepository,
)
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.discovery import discover
from betty.plugin.discovery.static import StaticDiscovery
from betty.plugin.ordered import OrderedPluginDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.plugin import DummyPlugin, DummyPluginOne, DummyPluginTwo


@PluginTypeDefinition(
    "ordered-plugin",
    base_cls=DummyPlugin,
    label="_OrderedPluginDefinition",
    label_plural="_OrderedPluginDefinitions",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _OrderedPluginDefinition(OrderedPluginDefinition[DummyPlugin]):
    pass


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


@PluginTypeDefinition(
    "dependent",
    base_cls=DummyPlugin,
    label="_DependentPluginDefinition",
    label_plural="_DependentPluginDefinition",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _DependentPluginDefinition(DependentPluginDefinition[DummyPlugin]):
    pass


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
        sut = PluginTypeDefinition(
            plugin_type_id,
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.id == plugin_type_id

    def test_base_cls(self) -> None:
        class _Plugin(Plugin):
            pass

        sut = PluginTypeDefinition(
            "-",
            base_cls=_Plugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.base_cls is _Plugin

    def test_cls(self) -> None:
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        with pytest.raises(ValueError):  # noqa: PT011
            sut.cls  # noqa: B018

    def test___call__(self) -> None:
        class _PluginDefinition(PluginDefinition):
            pass

        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        cls = sut(_PluginDefinition)
        assert sut.cls is cls
        with pytest.raises(ValueError):  # noqa: PT011
            sut(_PluginDefinition)

    def test_label(self) -> None:
        label = DUMMY_LOCALIZABLE
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=label,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.label is label

    def test_label_plural(self) -> None:
        label_plural = DUMMY_LOCALIZABLE
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = DUMMY_COUNTABLE_LOCALIZABLE
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=label_countable,
        )
        assert sut.label_countable is label_countable

    def test_description(self) -> None:
        description = DUMMY_LOCALIZABLE
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            description=description,
        )
        assert sut.description is description

    def test_discovery(self) -> None:
        discovery = StaticDiscovery()
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            discovery=discovery,
        )
        assert discovery in sut.discovery

    def test_add_discovery(self) -> None:
        discovery = StaticDiscovery()
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        sut.add_discovery(discovery)
        assert discovery in sut.discovery

    def test_override_discovery(self) -> None:
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert not sut.discovery
        with sut.override_discovery(StaticDiscovery(DummyPluginOne)):
            assert sut.discovery
        assert not sut.discovery

    async def test_add_discovery__during_override_discovery(self) -> None:
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        with sut.override_discovery(StaticDiscovery(DummyPluginOne)):
            sut.add_discovery(StaticDiscovery(DummyPluginTwo))
            assert DummyPluginTwo.plugin() not in await discover(None, *sut.discovery)
        assert DummyPluginOne.plugin() not in await discover(None, *sut.discovery)
        assert DummyPluginTwo.plugin() in await discover(None, *sut.discovery)

    def test_discovery_overridden(self) -> None:
        sut = PluginTypeDefinition(
            "-",
            base_cls=DummyPlugin,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert not sut.discovery_overridden
        with sut.override_discovery():
            assert sut.discovery_overridden
        assert not sut.discovery_overridden


class TestPluginDefinition:
    def test_id(self) -> None:
        id = "my-first-plugin"  # noqa: A001
        sut = PluginDefinition(id)
        assert sut.id == id

    def test_cls(self) -> None:
        sut = PluginDefinition("my-first-plugin")
        with pytest.raises(ValueError):  # noqa: PT011
            sut.cls  # noqa: B018

    def test___call__(self) -> None:
        class _Plugin(Plugin):
            pass

        sut = PluginDefinition("my-first-plugin")
        cls = sut(_Plugin)
        assert sut.cls is cls
        with pytest.raises(ValueError):  # noqa: PT011
            sut(_Plugin)

    def test_reference_label(self) -> None:
        id = "my-first-plugin"  # noqa: A001
        sut = PluginDefinition(id)
        actual = sut.reference_label.localize(DEFAULT_LOCALIZER)
        assert id in actual

    def test_reference_label_with_type(self) -> None:
        plugin_type_label = "My First Plugin Type"

        @PluginTypeDefinition(
            "my-first-plugin-type",
            base_cls=DummyPlugin,
            label=plugin_type_label,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        class _PluginDefinition(PluginDefinition[DummyPlugin]):
            pass

        id = "my-first-plugin"  # noqa: A001
        sut = _PluginDefinition(id)
        actual = sut.reference_label_with_type.localize(DEFAULT_LOCALIZER)
        assert id in actual
        assert plugin_type_label in actual


class TestPluginTypeRepository:
    def test___contains__(self) -> None:
        sut = PluginTypeRepository()
        assert "entity" in sut

    def test___getitem__(self) -> None:
        sut = PluginTypeRepository()
        assert sut["entity"].type().id == "entity"

    def test___iter__(self) -> None:
        sut = PluginTypeRepository()
        assert EntityDefinition in list(iter(sut))
