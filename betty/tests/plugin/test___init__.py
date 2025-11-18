from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, TypeAlias, TypeVar, cast

import pytest
from typing_extensions import override

from betty.app import App
from betty.locale.localizable import CountablePlain, Plain
from betty.plugin import (
    AppPluginRepositoryDefinition,
    ClassedPlugin,
    ClassedPluginDefinition,
    CountableHumanFacingPluginDefinition,
    CyclicDependencyError,
    DependentPluginDefinition,
    ExtensionPluginRepositoryDefinition,
    GlobalPluginRepositoryDefinition,
    HumanFacingPluginDefinition,
    OrderedPluginDefinition,
    PluginDefinition,
    PluginNotFound,
    PluginRepository,
    PluginTypeDefinition,
    ProjectPluginRepositoryDefinition,
    expand_plugin_dependencies,
    get_comes_after,
    get_comes_before,
    plugin_types,
    resolve_definition,
    resolve_id,
    sort_dependent_plugin_graph,
    sort_ordered_plugin_graph,
)
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.extension import Extension, ExtensionDefinition
from betty.test_utils.plugin import (
    DUMMY_PLUGIN_ONE,
    DUMMY_PLUGIN_THREE,
    DUMMY_PLUGIN_TWO,
    DummyPluginDefinition,
)
from betty.test_utils.project.extension import DummyExtension

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

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
            repositories=GlobalPluginRepositoryDefinition(
                lambda: StaticPluginRepository(_ClassedPluginDefinition)
            ),
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
            repositories=GlobalPluginRepositoryDefinition(
                lambda: StaticPluginRepository(_ClassedPluginDefinition)
            ),
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
    class _Sut(PluginRepository[DummyPluginDefinition]):
        def __init__(self, *plugins: DummyPluginDefinition):
            super().__init__(DummyPluginDefinition)
            self._plugins = {plugin.id: plugin for plugin in plugins}

        @override
        def get(self, plugin_id: MachineName) -> DummyPluginDefinition:
            try:
                return self._plugins[plugin_id]
            except KeyError:
                raise PluginNotFound(
                    DummyPluginDefinition.type, plugin_id, []
                ) from None

        @override
        def __iter__(self) -> Iterator[DummyPluginDefinition]:
            yield from self._plugins.values()

    def test___len__(self) -> None:
        sut = self._Sut(DUMMY_PLUGIN_ONE, DUMMY_PLUGIN_TWO, DUMMY_PLUGIN_THREE)
        assert len(sut) == 3

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
        repositories=GlobalPluginRepositoryDefinition(
            lambda: StaticPluginRepository(_OrderedPluginDefinition)
        ),
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
        repositories=GlobalPluginRepositoryDefinition(
            lambda: StaticPluginRepository(_DependentPluginDefinition)
        ),
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

    def test_repositories(self) -> None:
        repository = GlobalPluginRepositoryDefinition(
            StaticPluginRepository(PluginDefinition)
        )
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
            repositories=repository,
        )
        assert repository in sut.repositories

    def test_add_repository(self) -> None:
        repository = GlobalPluginRepositoryDefinition(
            StaticPluginRepository(PluginDefinition)
        )
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        sut.add_repository(repository)
        assert repository in sut.repositories

    def test_override_repositories(self) -> None:
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        assert not sut.repositories
        with sut.override_repositories(StaticPluginRepository(PluginDefinition)):
            assert sut.repositories
        assert not sut.repositories

    def test_add_repository__during_override_repositories(self) -> None:
        repository = GlobalPluginRepositoryDefinition(
            StaticPluginRepository(PluginDefinition)
        )
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        with sut.override_repositories(StaticPluginRepository(PluginDefinition)):
            overridden_repositories = sut.repositories
            sut.add_repository(repository)
            assert repository not in sut.repositories
        assert repository in sut.repositories
        for overridden_repository in overridden_repositories:
            assert overridden_repository not in sut.repositories

    def test_repositories_overridden(self) -> None:
        sut = PluginTypeDefinition(
            label=Plain("my-first-plugin-type"),
            id="my-first-plugin-type",
        )
        assert not sut.repositories_overridden
        with sut.override_repositories(StaticPluginRepository(PluginDefinition)):
            assert sut.repositories_overridden
        assert not sut.repositories_overridden  # type: ignore[unreachable]


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


GlobalPluginRepositoryDefinitionTestParams: TypeAlias = tuple[
    PluginRepository,
    Callable[[], Awaitable[PluginRepository[PluginDefinition]]]
    | Callable[[], PluginRepository[PluginDefinition]]
    | PluginRepository[PluginDefinition],
]


class TestGlobalPluginRepositoryDefinition:
    @staticmethod
    def _sut_params() -> Sequence[GlobalPluginRepositoryDefinitionTestParams]:
        repository = StaticPluginRepository(DummyPluginDefinition)

        async def _async_repository() -> PluginRepository:
            return repository

        return [
            (repository, repository),
            (repository, lambda: repository),
            (repository, _async_repository),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(
        self, request: pytest.FixtureRequest
    ) -> GlobalPluginRepositoryDefinitionTestParams:
        return cast(GlobalPluginRepositoryDefinitionTestParams, request.param)

    async def test___call___global(
        self, sut_params: GlobalPluginRepositoryDefinitionTestParams
    ) -> None:
        expected, definition = sut_params
        sut = GlobalPluginRepositoryDefinition(definition)
        assert await sut(None) is expected

    async def test___call____with_app(
        self, sut_params: GlobalPluginRepositoryDefinitionTestParams, temporary_app: App
    ) -> None:
        expected, definition = sut_params
        sut = GlobalPluginRepositoryDefinition(definition)
        assert await sut(temporary_app) is expected

    async def test___call____with_project(
        self, sut_params: GlobalPluginRepositoryDefinitionTestParams, temporary_app: App
    ) -> None:
        expected, definition = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = GlobalPluginRepositoryDefinition(definition)
            assert await sut(project) is expected


AppPluginRepositoryDefinitionTestParams: TypeAlias = tuple[
    PluginRepository,
    Callable[[App], Awaitable[PluginRepository[PluginDefinition]]]
    | Callable[[App], PluginRepository[PluginDefinition]],
]


class TestAppPluginRepositoryDefinition:
    @staticmethod
    def _sut_params() -> Sequence[AppPluginRepositoryDefinitionTestParams]:
        repository = StaticPluginRepository(DummyPluginDefinition)

        async def _async_repository(app: App) -> PluginRepository:
            return repository

        return [
            (repository, lambda app: repository),
            (repository, _async_repository),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(
        self, request: pytest.FixtureRequest
    ) -> AppPluginRepositoryDefinitionTestParams:
        return cast(AppPluginRepositoryDefinitionTestParams, request.param)

    async def test___call___global(
        self, sut_params: AppPluginRepositoryDefinitionTestParams
    ) -> None:
        expected, definition = sut_params
        sut = AppPluginRepositoryDefinition(definition)
        assert await sut(None) is None

    async def test___call____with_app(
        self, sut_params: AppPluginRepositoryDefinitionTestParams, temporary_app: App
    ) -> None:
        expected, definition = sut_params
        sut = AppPluginRepositoryDefinition(definition)
        assert await sut(temporary_app) is expected

    async def test___call____with_project(
        self, sut_params: AppPluginRepositoryDefinitionTestParams, temporary_app: App
    ) -> None:
        expected, definition = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = AppPluginRepositoryDefinition(definition)
            assert await sut(project) is expected


ProjectPluginRepositoryDefinitionTestParams: TypeAlias = tuple[
    PluginRepository,
    Callable[[Project], Awaitable[PluginRepository[PluginDefinition]]]
    | Callable[[Project], PluginRepository[PluginDefinition]],
]


class TestProjectPluginRepositoryDefinition:
    @staticmethod
    def _sut_params() -> Sequence[ProjectPluginRepositoryDefinitionTestParams]:
        repository = StaticPluginRepository(DummyPluginDefinition)

        async def _async_repository(project: Project) -> PluginRepository:
            return repository

        return [
            (repository, lambda project: repository),
            (repository, _async_repository),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(
        self, request: pytest.FixtureRequest
    ) -> ProjectPluginRepositoryDefinitionTestParams:
        return cast(ProjectPluginRepositoryDefinitionTestParams, request.param)

    async def test___call___global(
        self, sut_params: ProjectPluginRepositoryDefinitionTestParams
    ) -> None:
        expected, definition = sut_params
        sut = ProjectPluginRepositoryDefinition(definition)
        assert await sut(None) is None

    async def test___call____with_app(
        self,
        sut_params: ProjectPluginRepositoryDefinitionTestParams,
        temporary_app: App,
    ) -> None:
        expected, definition = sut_params
        sut = ProjectPluginRepositoryDefinition(definition)
        assert await sut(temporary_app) is None

    async def test___call____with_project(
        self,
        sut_params: ProjectPluginRepositoryDefinitionTestParams,
        temporary_app: App,
    ) -> None:
        expected, definition = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ProjectPluginRepositoryDefinition(definition)
            assert await sut(project) is expected


ExtensionPluginRepositoryDefinitionTestParams: TypeAlias = tuple[
    PluginRepository,
    Callable[[Extension], Awaitable[PluginRepository[PluginDefinition]]]
    | Callable[[Extension], PluginRepository[PluginDefinition]],
]


class TestExtensionPluginRepositoryDefinition:
    @staticmethod
    def _sut_params() -> Sequence[ExtensionPluginRepositoryDefinitionTestParams]:
        repository = StaticPluginRepository(DummyPluginDefinition)

        async def _async_repository(project: Extension) -> PluginRepository:
            return repository

        return [
            (repository, lambda project: repository),
            (repository, _async_repository),
        ]

    @pytest.fixture(params=_sut_params())
    def sut_params(
        self, request: pytest.FixtureRequest
    ) -> ExtensionPluginRepositoryDefinitionTestParams:
        return cast(ExtensionPluginRepositoryDefinitionTestParams, request.param)

    async def test___call___global(
        self, sut_params: ExtensionPluginRepositoryDefinitionTestParams
    ) -> None:
        expected, definition = sut_params
        sut = ExtensionPluginRepositoryDefinition(DummyExtension, definition)
        assert await sut(None) is None

    async def test___call____with_app(
        self,
        sut_params: ExtensionPluginRepositoryDefinitionTestParams,
        temporary_app: App,
    ) -> None:
        expected, definition = sut_params
        sut = ExtensionPluginRepositoryDefinition(DummyExtension, definition)
        assert await sut(temporary_app) is None

    async def test___call____with_project_without_extension(
        self,
        sut_params: ExtensionPluginRepositoryDefinitionTestParams,
        temporary_app: App,
    ) -> None:
        expected, definition = sut_params
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ExtensionPluginRepositoryDefinition(DummyExtension, definition)
            assert await sut(project) is None

    async def test___call____with_project_with_extension(
        self,
        sut_params: ExtensionPluginRepositoryDefinitionTestParams,
        temporary_app: App,
    ) -> None:
        expected, definition = sut_params
        with ExtensionDefinition.type.override_repositories(
            StaticPluginRepository(ExtensionDefinition, DummyExtension.plugin)
        ):
            async with Project.new_temporary(temporary_app) as project:
                project.configuration.extensions.enable(DummyExtension)
                async with project:
                    sut = ExtensionPluginRepositoryDefinition(
                        DummyExtension, definition
                    )
                    assert await sut(project) is expected
