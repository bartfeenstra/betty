from __future__ import annotations

from collections.abc import Awaitable, Callable, Collection, Iterable, Sequence
from importlib.metadata import EntryPoint, EntryPoints
from typing import TYPE_CHECKING, TypeAlias, TypeVar, cast

import pytest

from betty.app import App
from betty.locale.localizable import CountablePlain, Plain
from betty.plugin import (
    AppDiscovery,
    ClassedPlugin,
    ClassedPluginDefinition,
    CountableHumanFacingPluginDefinition,
    CyclicDependencyError,
    DependentPluginDefinition,
    EntryPointDiscovery,
    ExtensionDiscovery,
    GlobalDiscovery,
    HumanFacingPluginDefinition,
    OrderedPluginDefinition,
    PluginDefinition,
    PluginNotFound,
    PluginRepository,
    PluginTypeDefinition,
    ProjectDiscovery,
    StaticDiscovery,
    discover,
    expand_plugin_dependencies,
    get_comes_after,
    get_comes_before,
    plugin_types,
    resolve_definition,
    resolve_id,
    sort_dependent_plugin_graph,
    sort_ordered_plugin_graph,
)
from betty.project import Project
from betty.project.extension import Extension, ExtensionDefinition
from betty.test_utils.plugin import (
    DUMMY_PLUGIN_ONE,
    DUMMY_PLUGIN_THREE,
    DUMMY_PLUGIN_TWO,
    ClassedDummyPluginOne,
    ClassedDummyPluginTwo,
    DummyPluginDefinition,
)
from betty.test_utils.project.extension import DummyExtension

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.machine_name import MachineName

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


class TestPluginRepository:
    def test___len__(self) -> None:
        sut = PluginRepository(
            DummyPluginDefinition,
            DUMMY_PLUGIN_ONE,
            DUMMY_PLUGIN_TWO,
            DUMMY_PLUGIN_THREE,
        )
        assert len(sut) == 3

    def test___getitem__(self) -> None:
        sut = PluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE)
        assert sut[DUMMY_PLUGIN_ONE.id] is DUMMY_PLUGIN_ONE

    def test___iter__(self) -> None:
        sut = PluginRepository(
            DummyPluginDefinition,
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
        sut = PluginRepository(
            DummyPluginDefinition,
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
        PluginRepository(
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
        PluginRepository(
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
    plugin_repository = PluginRepository(
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
            PluginRepository(
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
            PluginRepository(
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

    def test_override_discoveries(self) -> None:
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        assert not sut.discoveries
        with sut.override_discoveries(DUMMY_PLUGIN_ONE):
            assert sut.discoveries
        assert not sut.discoveries

    async def test_add_discovery__during_override_discoveries(self) -> None:
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        with sut.override_discoveries(DUMMY_PLUGIN_ONE):
            sut.add_discovery(StaticDiscovery(DUMMY_PLUGIN_TWO))
            assert DUMMY_PLUGIN_TWO not in await discover(None, *sut.discoveries)
        assert DUMMY_PLUGIN_ONE not in await discover(None, *sut.discoveries)
        assert DUMMY_PLUGIN_TWO in await discover(None, *sut.discoveries)

    def test_discoveries_overridden(self) -> None:
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        assert not sut.discoveries_overridden
        with sut.override_discoveries():
            assert sut.discoveries_overridden
        assert not sut.discoveries_overridden  # type: ignore[unreachable]


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
            depends_on=depends_on,
            id="my-first-plugin",
        )
        assert sut.depends_on == depends_on

    def test_comes_after(self) -> None:
        depends_on = {"depends-on"}
        sut = DependentPluginDefinition(
            depends_on=depends_on,
            id="my-first-plugin",
        )
        assert sut.comes_after == depends_on


class TestOrderedPluginDefinition:
    def test_comes_before(self) -> None:
        comes_before = {"comes-before"}
        sut = OrderedPluginDefinition(comes_before=comes_before, id="my-first-plugin")
        assert sut.comes_before == comes_before

    def test_comes_after(self) -> None:
        comes_after = {"comes-after"}
        sut = OrderedPluginDefinition(comes_after=comes_after, id="my-first-plugin")
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


def test_plugin_types() -> None:
    assert plugin_types()


class TestStaticDiscovery:
    async def test_discover(self) -> None:
        sut = StaticDiscovery(DUMMY_PLUGIN_ONE)
        plugins = await sut.discover(None)
        assert DUMMY_PLUGIN_ONE in plugins


class TestEntryPointDiscovery:
    async def test_discover(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=ClassedDummyPluginOne.plugin.id,
                        value="betty.test_utils.plugin:ClassedDummyPluginOne",
                        group=entry_point_group,
                    ),
                    EntryPoint(
                        name=ClassedDummyPluginTwo.plugin.id,
                        value="betty.test_utils.plugin:ClassedDummyPluginTwo",
                        group=entry_point_group,
                    ),
                ]
            ),
        )
        sut = EntryPointDiscovery(entry_point_group)
        plugins = await sut.discover(None)
        assert ClassedDummyPluginOne.plugin in plugins
        assert ClassedDummyPluginTwo.plugin in plugins
        m_entry_points.assert_called_once_with(group=entry_point_group)


GlobalDiscoveryTestParams: TypeAlias = tuple[
    Collection[PluginDefinition],
    Callable[[], Awaitable[Iterable[PluginDefinition]]]
    | Callable[[], Iterable[PluginDefinition]],
]


class TestGlobalDiscovery:
    @staticmethod
    def _sut_params() -> Sequence[GlobalDiscoveryTestParams]:
        async def _async_discovery() -> Iterable[PluginDefinition]:
            return [DUMMY_PLUGIN_ONE]

        return [
            ([DUMMY_PLUGIN_ONE], lambda: [DUMMY_PLUGIN_ONE]),
            ([DUMMY_PLUGIN_ONE], _async_discovery),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(self, request: pytest.FixtureRequest) -> GlobalDiscoveryTestParams:
        return cast(GlobalDiscoveryTestParams, request.param)

    async def test_discover__global(
        self, sut_params: GlobalDiscoveryTestParams
    ) -> None:
        expected, discovery = sut_params
        sut = GlobalDiscovery(discovery)
        assert await sut.discover(None) == expected

    async def test_discover__with_app(
        self, sut_params: GlobalDiscoveryTestParams, temporary_app: App
    ) -> None:
        expected, discovery = sut_params
        sut = GlobalDiscovery(discovery)
        assert await sut.discover(temporary_app) == expected

    async def test_discover__with_project(
        self, sut_params: GlobalDiscoveryTestParams, temporary_app: App
    ) -> None:
        expected, discovery = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = GlobalDiscovery(discovery)
            assert await sut.discover(project) == expected


AppDiscoveryTestParams: TypeAlias = tuple[
    Collection[PluginDefinition],
    Callable[[App], Awaitable[Iterable[PluginDefinition]]]
    | Callable[[App], Iterable[PluginDefinition]],
]


class TestAppDiscovery:
    @staticmethod
    def _sut_params() -> Sequence[AppDiscoveryTestParams]:
        async def _async_discovery(app: App) -> Iterable[PluginDefinition]:
            return [DUMMY_PLUGIN_ONE]

        return [
            ([DUMMY_PLUGIN_ONE], lambda app: [DUMMY_PLUGIN_ONE]),
            ([DUMMY_PLUGIN_ONE], _async_discovery),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(self, request: pytest.FixtureRequest) -> AppDiscoveryTestParams:
        return cast(AppDiscoveryTestParams, request.param)

    async def test_discover_global(self, sut_params: AppDiscoveryTestParams) -> None:
        expected, discovery = sut_params
        sut = AppDiscovery(discovery)
        assert not list(await sut.discover(None))

    async def test_discover__with_app(
        self, sut_params: AppDiscoveryTestParams, temporary_app: App
    ) -> None:
        expected, discovery = sut_params
        sut = AppDiscovery(discovery)
        assert await sut.discover(temporary_app) == expected

    async def test_discover__with_project(
        self, sut_params: AppDiscoveryTestParams, temporary_app: App
    ) -> None:
        expected, discovery = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = AppDiscovery(discovery)
            assert await sut.discover(project) == expected


ProjectDiscoveryTestParams: TypeAlias = tuple[
    Collection[PluginDefinition],
    Callable[[Project], Awaitable[Iterable[PluginDefinition]]]
    | Callable[[Project], Iterable[PluginDefinition]],
]


class TestProjectDiscovery:
    @staticmethod
    def _sut_params() -> Sequence[ProjectDiscoveryTestParams]:
        async def _async_discovery(project: Project) -> Iterable[PluginDefinition]:
            return [DUMMY_PLUGIN_ONE]

        return [
            ([DUMMY_PLUGIN_ONE], lambda project: [DUMMY_PLUGIN_ONE]),
            ([DUMMY_PLUGIN_ONE], _async_discovery),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(self, request: pytest.FixtureRequest) -> ProjectDiscoveryTestParams:
        return cast(ProjectDiscoveryTestParams, request.param)

    async def test_discover_global(
        self, sut_params: ProjectDiscoveryTestParams
    ) -> None:
        expected, discovery = sut_params
        sut = ProjectDiscovery(discovery)
        assert not list(await sut.discover(None))

    async def test_discover__with_app(
        self,
        sut_params: ProjectDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        sut = ProjectDiscovery(discovery)
        assert not list(await sut.discover(temporary_app))

    async def test_discover__with_project(
        self,
        sut_params: ProjectDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ProjectDiscovery(discovery)
            assert await sut.discover(project) == expected


ExtensionDiscoveryTestParams: TypeAlias = tuple[
    Collection[PluginDefinition],
    Callable[[Extension], Awaitable[Iterable[PluginDefinition]]]
    | Callable[[Extension], Iterable[PluginDefinition]],
]


class TestExtensionDiscovery:
    @staticmethod
    def _sut_params() -> Sequence[ExtensionDiscoveryTestParams]:
        async def _async_discovery(project: Extension) -> Iterable[PluginDefinition]:
            return [DUMMY_PLUGIN_ONE]

        return [
            ([DUMMY_PLUGIN_ONE], lambda project: [DUMMY_PLUGIN_ONE]),
            ([DUMMY_PLUGIN_ONE], _async_discovery),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(
        self, request: pytest.FixtureRequest
    ) -> ExtensionDiscoveryTestParams:
        return cast(ExtensionDiscoveryTestParams, request.param)

    async def test_discover_global(
        self, sut_params: ExtensionDiscoveryTestParams
    ) -> None:
        expected, discovery = sut_params
        sut = ExtensionDiscovery(DummyExtension, discovery)
        assert not list(await sut.discover(None))

    async def test_discover__with_app(
        self,
        sut_params: ExtensionDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        sut = ExtensionDiscovery(DummyExtension, discovery)
        assert not list(await sut.discover(temporary_app))

    async def test_discover__with_project_without_extension(
        self,
        sut_params: ExtensionDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ExtensionDiscovery(DummyExtension, discovery)
            assert not list(await sut.discover(project))

    async def test_discover__with_project_with_extension(
        self,
        sut_params: ExtensionDiscoveryTestParams,
        temporary_app: App,
    ) -> None:
        expected, discovery = sut_params
        with ExtensionDefinition.type.override_discoveries(DummyExtension.plugin):
            async with Project.new_temporary(temporary_app) as project:
                project.configuration.extensions.enable(DummyExtension)
                async with project:
                    sut = ExtensionDiscovery(DummyExtension, discovery)
                    assert await sut.discover(project) == expected


async def test_discover() -> None:
    assert DUMMY_PLUGIN_ONE in await discover(None, StaticDiscovery(DUMMY_PLUGIN_ONE))
