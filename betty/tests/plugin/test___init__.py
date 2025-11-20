from __future__ import annotations

from typing import TypeVar

from betty.locale.localizable import CountablePlain, Plain
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    CountableHumanFacingPluginDefinition,
    CyclicDependencyError,
    HumanFacingPluginDefinition,
    PluginDefinition,
    PluginNotFound,
    PluginTypeDefinition,
    plugin_types,
    resolve_definition,
    resolve_id,
)
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.discovery import discover
from betty.plugin.discovery.static import StaticDiscovery
from betty.plugin.ordered import OrderedPluginDefinition
from betty.test_utils.plugin import (
    DUMMY_PLUGIN_ONE,
    DUMMY_PLUGIN_TWO,
    DummyPluginDefinition,
)

_T = TypeVar("_T")


def test_resolve_definition__with_plugin_cls() -> None:
    plugin_id = "my-first-plugin-id"

    class _ClassedPluginCls:
        pass

    class _ClassedPluginDefinition(ClassedPluginDefinition[_ClassedPluginCls]):
        plugin_type_cls = _ClassedPluginCls
        type = PluginTypeDefinition(
            id="-",
            label=Plain(""),
        )

    @_ClassedPluginDefinition(id=plugin_id)
    class _ClassedPlugin(_ClassedPluginCls, ClassedPlugin):
        pass

    assert resolve_definition(_ClassedPlugin) is _ClassedPlugin.plugin


def test_resolve_definition__with_plugin_definition() -> None:
    definition = PluginDefinition(id="my-first-plugin-id")
    assert resolve_definition(definition) is definition


def test_resolve_id__with_plugin_cls() -> None:
    plugin_id = "my-first-plugin-id"

    class _ClassedPluginCls:
        pass

    class _ClassedPluginDefinition(ClassedPluginDefinition[_ClassedPluginCls]):
        plugin_type_cls = _ClassedPluginCls
        type = PluginTypeDefinition(
            id="-",
            label=Plain(""),
        )

    @_ClassedPluginDefinition(id=plugin_id)
    class _ClassedPlugin(_ClassedPluginCls, ClassedPlugin):
        pass

    assert resolve_id(_ClassedPlugin) == plugin_id


def test_resolve_id__with_plugin_definition() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_id(PluginDefinition(id=plugin_id)) == plugin_id


def test_resolve_id__with_plugin_id() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_id(plugin_id) == plugin_id


class TestPluginNotFound:
    async def test_new__without_available_plugins(self) -> None:
        unknown_plugin = "my-first-plugin-id"
        sut = PluginNotFound(DummyPluginDefinition.type, unknown_plugin, [])
        assert unknown_plugin in str(sut)

    async def test_new__with_available_plugins(self) -> None:
        unknown_plugin = "my-first-plugin-id"
        available_plugin = "my-first-available-plugin-id"
        sut = PluginNotFound(
            DummyPluginDefinition.type, unknown_plugin, [available_plugin]
        )
        assert unknown_plugin in str(sut)
        assert available_plugin in str(sut)


class TestCyclicDependencyError:
    def test(self) -> None:
        plugin_id = "my-first-plugin"
        sut = CyclicDependencyError([plugin_id])
        assert plugin_id in str(sut)


class _OrderedPluginDefinition(OrderedPluginDefinition):
    type = PluginTypeDefinition(
        id="ordered-plugin",
        label=Plain(""),
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
        label=Plain("_ExpandPluginDependenciesTestPluginDefinition"),
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
            label=Plain(""),
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
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
            discoveries=discovery,
        )
        assert discovery in sut.discoveries

    def test_add_discovery(self) -> None:
        discovery = StaticDiscovery()
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        sut.add_discovery(discovery)
        assert discovery in sut.discoveries

    def test_override_discovery(self) -> None:
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        assert not sut.discoveries
        with sut.override_discovery(DUMMY_PLUGIN_ONE):
            assert sut.discoveries
        assert not sut.discoveries

    async def test_add_discovery__during_override_discovery(self) -> None:
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        with sut.override_discovery(DUMMY_PLUGIN_ONE):
            sut.add_discovery(StaticDiscovery(DUMMY_PLUGIN_TWO))
            assert DUMMY_PLUGIN_TWO not in await discover(None, *sut.discoveries)
        assert DUMMY_PLUGIN_ONE not in await discover(None, *sut.discoveries)
        assert DUMMY_PLUGIN_TWO in await discover(None, *sut.discoveries)

    def test_discovery_overridden(self) -> None:
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        assert not sut.discovery_overridden
        with sut.override_discovery():
            assert sut.discovery_overridden
        assert not sut.discovery_overridden  # type: ignore[unreachable]


class TestClassedPluginDefinition:
    def test_cls(self) -> None:
        class _Cls:
            pass

        sut = ClassedPluginDefinition(cls=_Cls, id="my-first-plugin")
        assert sut.cls is _Cls

    def test___call__(self) -> None:
        class _Cls:
            pass

        sut = ClassedPluginDefinition[_Cls](id="my-first-plugin")
        sut(_Cls)
        assert sut.cls is _Cls


class TestCountableHumanFacingPluginDefinition:
    def test_label_plural(self) -> None:
        label_plural = Plain("")
        sut = CountableHumanFacingPluginDefinition(
            label_plural=label_plural,
            label_countable=CountablePlain("", ""),
            id="my-first-plugin",
            label=Plain(""),
        )
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = CountablePlain("", "")
        sut = CountableHumanFacingPluginDefinition(
            label_countable=label_countable,
            label_plural=Plain(""),
            id="my-first-plugin",
            label=Plain(""),
        )
        assert sut.label_countable is label_countable


class TestPluginDefinition:
    def test_id(self) -> None:
        id = "my-first-plugin"  # noqa A001
        sut = PluginDefinition(id=id)
        assert sut.id == id


class TestHumanFacingPluginDefinition:
    def test_label(self) -> None:
        label = Plain("")
        sut = HumanFacingPluginDefinition(label=label, id="my-first-plugin")
        assert sut.label is label

    def test_description(self) -> None:
        description = Plain("")
        sut = HumanFacingPluginDefinition(
            description=description, id="my-first-plugin", label=Plain("")
        )
        assert sut.description is description


def test_plugin_types() -> None:
    assert plugin_types()
