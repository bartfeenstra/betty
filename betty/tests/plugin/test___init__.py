from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, TypeVar

import pytest
from typing_extensions import override

from betty.locale.localizable import CountablePlain, Plain
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    CountableHumanFacingPluginDefinition,
    CyclicDependencyError,
    DependentPluginDefinition,
    HumanFacingPluginDefinition,
    OrderedPluginDefinition,
    PluginDefinition,
    PluginNotFound,
    PluginRepository,
    PluginTypeDefinition,
    expand_plugin_dependencies,
    get_comes_after,
    get_comes_before,
    resolve_identifier,
    sort_dependent_plugin_graph,
    sort_ordered_plugin_graph,
)
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import (
    DUMMY_PLUGIN_ONE,
    DUMMY_PLUGIN_THREE,
    DUMMY_PLUGIN_TWO,
    DummyPluginDefinition,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from betty.machine_name import MachineName

_T = TypeVar("_T")


def test_resolve_identifier__with_plugin_cls() -> None:
    plugin_id = "my-first-plugin-id"

    class _ClassedPluginCls:
        pass

    class _ClassedPluginDefinition(ClassedPluginDefinition[_ClassedPluginCls]):
        type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
            id="-", cls=_ClassedPluginCls, label=Plain("")
        )

    @_ClassedPluginDefinition(id=plugin_id)
    class _ClassedPlugin(_ClassedPluginCls, ClassedPlugin):
        pass

    assert resolve_identifier(_ClassedPlugin) == plugin_id


def test_resolve_identifier__with_plugin_definition() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_identifier(PluginDefinition(id=plugin_id)) == plugin_id


def test_resolve_identifier__with_plugin_id() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_identifier(plugin_id) == plugin_id


class TestPluginNotFound:
    async def test_new__without_available_plugins(self) -> None:
        unknown_plugin = "my-first-plugin-id"
        sut = PluginNotFound.new(unknown_plugin, [])
        assert unknown_plugin in str(sut)

    async def test_new__with_available_plugins(self) -> None:
        unknown_plugin = "my-first-plugin-id"
        available_plugin = "my-first-available-plugin-id"
        sut = PluginNotFound.new(unknown_plugin, [available_plugin])
        assert unknown_plugin in str(sut)
        assert available_plugin in str(sut)


class TestPluginRepository:
    class _Sut(PluginRepository[DummyPluginDefinition]):
        def __init__(self, *plugins: DummyPluginDefinition):
            super().__init__(DummyPluginDefinition)
            self._plugins = {plugin.id: plugin for plugin in plugins}

        @override
        def get(self, plugin_id: MachineName) -> DummyPluginDefinition:
            try:
                return self._plugins[plugin_id]
            except KeyError:
                raise PluginNotFound.new(plugin_id, []) from None

        @override
        def __iter__(self) -> Iterator[DummyPluginDefinition]:
            yield from self._plugins.values()

    def test___getitem__(self) -> None:
        sut = self._Sut(DUMMY_PLUGIN_ONE)
        assert sut[DUMMY_PLUGIN_ONE.id] is DUMMY_PLUGIN_ONE

    def test___iter__(self) -> None:
        sut = self._Sut(
            DUMMY_PLUGIN_ONE,
            DUMMY_PLUGIN_TWO,
            DUMMY_PLUGIN_THREE,
        )
        assert list(iter(sut)) == [
            DUMMY_PLUGIN_ONE,
            DUMMY_PLUGIN_TWO,
            DUMMY_PLUGIN_THREE,
        ]

    def test_plugin_id_schema(self) -> None:
        sut = self._Sut(
            DUMMY_PLUGIN_ONE,
            DUMMY_PLUGIN_TWO,
            DUMMY_PLUGIN_THREE,
        )
        actual = sut.plugin_id_schema
        assert actual.schema["enum"] == [
            "dummy-plugin-one",
            "dummy-plugin-two",
            "dummy-plugin-three",
        ]


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


@pytest.mark.parametrize(
    ("expected", "plugins"),
    [
        (
            [],
            [],
        ),
        (
            [_ORDERED_PLUGIN_ISOLATED.id],
            [_ORDERED_PLUGIN_ISOLATED],
        ),
        (
            [_ORDERED_PLUGIN_HAS_COMES_AFTER.id],
            [_ORDERED_PLUGIN_HAS_COMES_AFTER],
        ),
        (
            [
                _ORDERED_PLUGIN_COMES_AFTER_TARGET.id,
                _ORDERED_PLUGIN_HAS_COMES_AFTER.id,
            ],
            [
                _ORDERED_PLUGIN_COMES_AFTER_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_AFTER,
            ],
        ),
        (
            [_ORDERED_PLUGIN_HAS_COMES_BEFORE.id],
            [_ORDERED_PLUGIN_HAS_COMES_BEFORE],
        ),
        (
            [
                _ORDERED_PLUGIN_HAS_COMES_BEFORE.id,
                _ORDERED_PLUGIN_COMES_BEFORE_TARGET.id,
            ],
            [
                _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_BEFORE,
            ],
        ),
    ],
)
async def test_sort_ordered_plugin_graph(
    expected: list[MachineName],
    plugins: Iterable[_OrderedPluginDefinition],
) -> None:
    sorter = await sort_ordered_plugin_graph(
        StaticPluginRepository(
            _OrderedPluginDefinition,
            _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
            _ORDERED_PLUGIN_HAS_COMES_BEFORE,
            _ORDERED_PLUGIN_COMES_AFTER_TARGET,
            _ORDERED_PLUGIN_HAS_COMES_AFTER,
            _ORDERED_PLUGIN_ISOLATED,
        ),
        plugins,
    )
    assert list(sorter.static_order()) == expected


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


@pytest.mark.parametrize(
    ("expected", "plugins"),
    [
        (
            set(),
            set(),
        ),
        (
            {
                _DEPENDENT_PLUGIN_ISOLATED,
            },
            {
                _DEPENDENT_PLUGIN_ISOLATED,
            },
        ),
        (
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            },
            {
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
        (
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            },
            {
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            },
        ),
        (
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
        (
            {_DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT},
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
    ],
)
async def test_expand_plugin_dependencies(
    expected: set[_DependentPluginDefinition],
    plugins: set[_DependentPluginDefinition],
) -> None:
    actual = await expand_plugin_dependencies(
        StaticPluginRepository(
            _DependentPluginDefinition,
            _DEPENDENT_PLUGIN_ISOLATED,
            _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
            _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
        ),
        plugins,
    )
    assert actual == expected


@pytest.mark.parametrize(
    ("expected", "plugins"),
    [
        (
            [],
            set(),
        ),
        (
            [
                _DEPENDENT_PLUGIN_ISOLATED.id,
            ],
            {
                _DEPENDENT_PLUGIN_ISOLATED,
            },
        ),
        (
            [
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT.id,
            ],
            {
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
        (
            [
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT.id,
            ],
            {
                _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
            },
        ),
        (
            [
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT.id,
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT.id,
            ],
            {
                _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
            },
        ),
        (
            [_DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT.id],
            {
                _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
            },
        ),
    ],
)
async def test_sort_dependent_plugin_graph(
    expected: list[MachineName], plugins: Iterable[_DependentPluginDefinition]
) -> None:
    plugin_repository = StaticPluginRepository(
        _DependentPluginDefinition,
        _DEPENDENT_PLUGIN_ISOLATED,
        _DEPENDENT_PLUGIN_UPSTREAM_DEPENDENT,
        _DEPENDENT_PLUGIN_UPSTREAM_AND_DOWNSTREAM_DEPENDENT,
        _DEPENDENT_PLUGIN_DOWNSTREAM_DEPENDENT,
    )
    sorter = await sort_dependent_plugin_graph(plugin_repository, plugins)
    assert list(sorter.static_order()) == expected


@pytest.mark.parametrize(
    ("expected", "origin"),
    [
        (
            set(),
            _ORDERED_PLUGIN_ISOLATED,
        ),
        (
            {_ORDERED_PLUGIN_COMES_BEFORE_TARGET},
            _ORDERED_PLUGIN_HAS_COMES_BEFORE,
        ),
        (
            {_ORDERED_PLUGIN_HAS_COMES_AFTER},
            _ORDERED_PLUGIN_COMES_AFTER_TARGET,
        ),
        (
            {_ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL},
            _ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL,
        ),
    ],
)
def test_get_comes_before(
    expected: set[_OrderedPluginDefinition], origin: _OrderedPluginDefinition
) -> None:
    assert (
        get_comes_before(
            StaticPluginRepository(
                _OrderedPluginDefinition,
                _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_BEFORE,
                _ORDERED_PLUGIN_COMES_AFTER_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_AFTER,
                _ORDERED_PLUGIN_ISOLATED,
                _ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL,
                _ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL,
            ),
            origin,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("expected", "origin"),
    [
        (
            set(),
            _ORDERED_PLUGIN_ISOLATED,
        ),
        (
            {_ORDERED_PLUGIN_COMES_AFTER_TARGET},
            _ORDERED_PLUGIN_HAS_COMES_AFTER,
        ),
        (
            {_ORDERED_PLUGIN_HAS_COMES_BEFORE},
            _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
        ),
        (
            {_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL},
            _ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL,
        ),
    ],
)
def test_get_comes_after(
    expected: set[_OrderedPluginDefinition], origin: _OrderedPluginDefinition
) -> None:
    assert (
        get_comes_after(
            StaticPluginRepository(
                _OrderedPluginDefinition,
                _ORDERED_PLUGIN_COMES_BEFORE_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_BEFORE,
                _ORDERED_PLUGIN_COMES_AFTER_TARGET,
                _ORDERED_PLUGIN_HAS_COMES_AFTER,
                _ORDERED_PLUGIN_ISOLATED,
                _ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL,
                _ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL,
            ),
            origin,
        )
        == expected
    )


class TestPluginTypeDefinition:
    def test_id(self) -> None:
        plugin_type_id = "my-first-plugin-type"
        sut = PluginTypeDefinition(id=plugin_type_id, label=Plain(""))
        assert sut.id == plugin_type_id

    def test_label(self) -> None:
        label = Plain("my-first-plugin-type")
        sut = PluginTypeDefinition(label=label, id="my-first-plugin-type")
        assert sut.label is label


class TestClassedPluginTypeDefinition:
    def test_cls(self) -> None:
        class _Cls:
            pass

        sut = ClassedPluginTypeDefinition(
            cls=_Cls, id="my-first-plugin-type", label=Plain("")
        )
        assert sut.cls is _Cls


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


class TestDependentPluginDefinition:
    def test_depends_on(self) -> None:
        depends_on = {"depends-on"}
        sut = DependentPluginDefinition(
            depends_on=depends_on,  # type: ignore[arg-type]
            id="my-first-plugin",
        )
        assert sut.depends_on == depends_on

    def test_comes_after(self) -> None:
        depends_on = {"depends-on"}
        sut = DependentPluginDefinition(
            depends_on=depends_on,  # type: ignore[arg-type]
            id="my-first-plugin",
        )
        assert sut.comes_after == depends_on


class TestOrderedPluginDefinition:
    def test_comes_before(self) -> None:
        comes_before = {"comes-before"}
        sut = DependentPluginDefinition(comes_before=comes_before, id="my-first-plugin")
        assert sut.comes_before == comes_before

    def test_comes_after(self) -> None:
        comes_after = {"comes-after"}
        sut = DependentPluginDefinition(comes_after=comes_after, id="my-first-plugin")
        assert sut.comes_after == comes_after


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
