from __future__ import annotations

from graphlib import TopologicalSorter
from typing import Self, Literal, TYPE_CHECKING, TypeVar

import pytest
from typing_extensions import override

from betty.factory import Factory, new
from betty.json.schema import Schema
from betty.plugin import (
    PluginNotFound,
    Plugin,
    PluginRepository,
    PluginIdToTypeMapping,
    sort_ordered_plugin_graph,
    PluginIdentifier,
    OrderedPlugin,
    DependentPlugin,
    sort_dependent_plugin_graph,
    CyclicDependencyError,
    resolve_identifier,
)
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import DummyPlugin

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from collections.abc import AsyncIterator, Sequence

_T = TypeVar("_T")


def test_resolve_identifier__with_plugin() -> None:
    assert resolve_identifier(DummyPlugin) == DummyPlugin.plugin_id()


def test_resolve_identifier__with_plugin_id() -> None:
    assert resolve_identifier(DummyPlugin.plugin_id()) == DummyPlugin.plugin_id()


class TestPluginNotFound:
    async def test_new(self) -> None:
        PluginNotFound.new("my-first-plugin-id", [])


class TestPlugin:
    async def test_plugin_description(self) -> None:
        Plugin.plugin_description()


class _TestPluginRepositoryMixinOne:
    pass


class _TestPluginRepositoryMixinTwo:
    pass


class _TestPluginRepositoryMixinThree:
    pass


class _TestPluginRepositoryPluginOne(DummyPlugin, _TestPluginRepositoryMixinOne):
    pass


class _TestPluginRepositoryPluginOneTwo(
    DummyPlugin,
    _TestPluginRepositoryMixinOne,
    _TestPluginRepositoryMixinTwo,
):
    pass


class _TestPluginRepositoryPluginOneTwoThree(
    DummyPlugin,
    _TestPluginRepositoryMixinOne,
    _TestPluginRepositoryMixinTwo,
    _TestPluginRepositoryMixinThree,
):
    pass


class _TestPluginRepositoryPluginDefaultFactory(DummyPlugin):
    pass


class _TestPluginRepositoryPluginCustomFactory(DummyPlugin):
    def __init__(self, must_be_true: Literal[True]):
        assert must_be_true

    @classmethod
    def new_custom(cls) -> Self:
        return cls(True)


class _TestPluginRepositoryPluginRepository(PluginRepository[DummyPlugin]):
    def __init__(
        self,
        *plugins: type[DummyPlugin],
        factory: Factory | None = None,
        schema_template: Schema | None = None,
    ):
        super().__init__(factory=factory, schema_template=schema_template)
        self._plugins = {plugin.plugin_id(): plugin for plugin in plugins}

    @override
    async def get(self, plugin_id: MachineName) -> type[DummyPlugin]:
        try:
            return self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFound.new(plugin_id, []) from None

    @override
    async def __aiter__(self) -> AsyncIterator[type[DummyPlugin]]:
        for plugin in self._plugins.values():
            yield plugin


class TestPluginIdToTypeMapping:
    async def test_new(self) -> None:
        await PluginIdToTypeMapping.new(StaticPluginRepository())

    async def test_get(self) -> None:
        sut = await PluginIdToTypeMapping.new(StaticPluginRepository(DummyPlugin))
        assert sut.get(DummyPlugin.plugin_id()) is DummyPlugin

    async def test___getitem__(self) -> None:
        sut = await PluginIdToTypeMapping.new(StaticPluginRepository(DummyPlugin))
        assert sut[DummyPlugin.plugin_id()] is DummyPlugin

    async def test___iter__(self) -> None:
        sut = await PluginIdToTypeMapping.new(StaticPluginRepository(DummyPlugin))
        assert list(iter(sut)) == [DummyPlugin.plugin_id()]


class TestPluginRepository:
    async def test_resolve_identifier__with_unknown_plugin_id(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        with pytest.raises(PluginNotFound):
            await sut.resolve_identifier("unknown-plugin")

    async def test_resolve_identifier__with_known_plugin_id(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(_TestPluginRepositoryPluginOne)
        assert (
            await sut.resolve_identifier(_TestPluginRepositoryPluginOne.plugin_id())
            == _TestPluginRepositoryPluginOne
        )

    async def test_resolve_identifier__with_known_plugin(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(_TestPluginRepositoryPluginOne)
        assert (
            await sut.resolve_identifier(_TestPluginRepositoryPluginOne)
            is _TestPluginRepositoryPluginOne
        )

    async def test_resolve_identifiers__without_identifiers(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        assert await sut.resolve_identifiers([]) == []

    async def test_resolve_identifiers__with_unknown_plugin_id(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        with pytest.raises(PluginNotFound):
            await sut.resolve_identifiers(["unknown-plugin"])

    async def test_resolve_identifiers__with_known_plugin_id(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(_TestPluginRepositoryPluginOne)
        assert await sut.resolve_identifiers(
            [_TestPluginRepositoryPluginOne.plugin_id()]
        ) == [_TestPluginRepositoryPluginOne]

    async def test_resolve_identifiers__with_known_plugin(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(_TestPluginRepositoryPluginOne)
        assert await sut.resolve_identifiers([_TestPluginRepositoryPluginOne]) == [
            _TestPluginRepositoryPluginOne
        ]

    async def test_mapping__without_plugins(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        await sut.mapping()

    async def test_mapping__with_plugins(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginOne,
            _TestPluginRepositoryPluginOneTwo,
            _TestPluginRepositoryPluginOneTwoThree,
        )
        plugin_id_to_type_mapping = await sut.mapping()
        assert (
            plugin_id_to_type_mapping[_TestPluginRepositoryPluginOne.plugin_id()]
            is _TestPluginRepositoryPluginOne
        )

    async def test_select__without_plugins(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        assert len(await sut.select()) == 0

    @pytest.mark.parametrize(
        (
            "expected",
            "mixins",
        ),
        [
            (
                (
                    _TestPluginRepositoryPluginOne,
                    _TestPluginRepositoryPluginOneTwo,
                    _TestPluginRepositoryPluginOneTwoThree,
                ),
                {},
            ),
            (
                (
                    _TestPluginRepositoryPluginOne,
                    _TestPluginRepositoryPluginOneTwo,
                    _TestPluginRepositoryPluginOneTwoThree,
                ),
                {_TestPluginRepositoryMixinOne},
            ),
            (
                (
                    _TestPluginRepositoryPluginOneTwo,
                    _TestPluginRepositoryPluginOneTwoThree,
                ),
                {_TestPluginRepositoryMixinOne, _TestPluginRepositoryMixinTwo},
            ),
            (
                (_TestPluginRepositoryPluginOneTwoThree,),
                {
                    _TestPluginRepositoryMixinOne,
                    _TestPluginRepositoryMixinTwo,
                    _TestPluginRepositoryMixinThree,
                },
            ),
            (
                (
                    _TestPluginRepositoryPluginOneTwo,
                    _TestPluginRepositoryPluginOneTwoThree,
                ),
                {_TestPluginRepositoryMixinTwo},
            ),
            (
                (_TestPluginRepositoryPluginOneTwoThree,),
                {_TestPluginRepositoryMixinTwo, _TestPluginRepositoryMixinThree},
            ),
            (
                (_TestPluginRepositoryPluginOneTwoThree,),
                {_TestPluginRepositoryMixinThree},
            ),
        ],
    )
    async def test_select__with_mixins(
        self,
        expected: Sequence[type[DummyPlugin]],
        mixins: set[
            _TestPluginRepositoryMixinOne
            | _TestPluginRepositoryMixinTwo
            | _TestPluginRepositoryMixinThree
        ],
    ) -> None:
        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginOne,
            _TestPluginRepositoryPluginOneTwo,
            _TestPluginRepositoryPluginOneTwoThree,
        )

        assert list(await sut.select(*mixins)) == list(expected)

    async def test_new_target__with_default_factory(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginDefaultFactory
        )
        assert isinstance(
            await sut.new_target(_TestPluginRepositoryPluginDefaultFactory),
            _TestPluginRepositoryPluginDefaultFactory,
        )
        assert isinstance(
            await sut.new_target(_TestPluginRepositoryPluginDefaultFactory.plugin_id()),
            _TestPluginRepositoryPluginDefaultFactory,
        )

    async def test_new_target__with_custom_factory(self) -> None:
        async def factory(
            cls: type[_T],
        ) -> _T:
            return (
                cls.new_custom()  # type: ignore[return-value]
                if issubclass(cls, _TestPluginRepositoryPluginCustomFactory)
                else await new(cls)  # type: ignore[arg-type]
            )

        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginCustomFactory, factory=factory
        )
        assert isinstance(
            await sut.new_target(_TestPluginRepositoryPluginCustomFactory),
            _TestPluginRepositoryPluginCustomFactory,
        )
        assert isinstance(
            await sut.new_target(_TestPluginRepositoryPluginCustomFactory.plugin_id()),
            _TestPluginRepositoryPluginCustomFactory,
        )

    async def test_plugin_id_schema(self) -> None:
        def_name = "myFirstSchema"
        title = "My First Schema"
        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginOne,
            _TestPluginRepositoryPluginOneTwo,
            _TestPluginRepositoryPluginOneTwoThree,
            schema_template=Schema(def_name=def_name, title=title),
        )
        actual = await sut.plugin_id_schema
        assert actual.def_name == def_name
        assert actual.schema["title"] == title
        assert actual.schema["enum"] == [
            "test-plugin-repository-plugin-one",
            "test-plugin-repository-plugin-one-two",
            "test-plugin-repository-plugin-one-two-three",
        ]


class _DummyOrderedPlugin(OrderedPlugin["_DummyOrderedPlugin"], DummyPlugin):
    pass


class ComesBeforeTargetPlugin(_DummyOrderedPlugin):
    pass


class HasComesBeforePlugin(_DummyOrderedPlugin):
    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[_DummyOrderedPlugin]]:
        return {ComesBeforeTargetPlugin}


class ComesAfterTargetPlugin(_DummyOrderedPlugin):
    pass


class HasComesAfterPlugin(_DummyOrderedPlugin):
    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[_DummyOrderedPlugin]]:
        return {ComesAfterTargetPlugin}


class IsolatedOrderedPluginOne(_DummyOrderedPlugin):
    pass


class IsolatedOrderedPluginTwo(_DummyOrderedPlugin):
    pass


@pytest.mark.parametrize(
    ("expected", "initial"),
    [
        (
            [],
            [],
        ),
        (
            [IsolatedOrderedPluginOne, IsolatedOrderedPluginTwo],
            [IsolatedOrderedPluginOne, IsolatedOrderedPluginTwo],
        ),
        (
            [HasComesAfterPlugin],
            [HasComesAfterPlugin],
        ),
        (
            [ComesAfterTargetPlugin, HasComesAfterPlugin],
            [ComesAfterTargetPlugin, HasComesAfterPlugin],
        ),
        (
            [HasComesBeforePlugin],
            [HasComesBeforePlugin],
        ),
        (
            [HasComesBeforePlugin, ComesBeforeTargetPlugin],
            [ComesBeforeTargetPlugin, HasComesBeforePlugin],
        ),
    ],
)
async def test_sort_ordered_plugin_graph(
    expected: list[type[_DummyOrderedPlugin]],
    initial: Sequence[type[_DummyOrderedPlugin]],
) -> None:
    sorter = TopologicalSorter[type[_DummyOrderedPlugin]]()
    await sort_ordered_plugin_graph(
        sorter,
        StaticPluginRepository[_DummyOrderedPlugin](
            ComesBeforeTargetPlugin,
            HasComesBeforePlugin,
            ComesAfterTargetPlugin,
            HasComesAfterPlugin,
            IsolatedOrderedPluginOne,
            IsolatedOrderedPluginTwo,
        ),
        initial,
    )
    assert list(sorter.static_order()) == expected


class _DummyDependentPlugin(DependentPlugin["_DummyDependentPlugin"], DummyPlugin):
    pass


class DownStream(_DummyDependentPlugin):
    pass


class Upstream(_DummyDependentPlugin):
    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[_DummyDependentPlugin]]:
        return {UpstreamAndDownstream}


class UpstreamAndDownstream(_DummyDependentPlugin):
    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[_DummyDependentPlugin]]:
        return {DownStream}


class IsolatedDependentPluginOne(_DummyDependentPlugin):
    pass


class IsolatedDependentPluginTwo(_DummyDependentPlugin):
    pass


@pytest.mark.parametrize(
    ("expected", "updated", "initial"),
    [
        (
            [],
            [],
            [],
        ),
        (
            [IsolatedDependentPluginOne, IsolatedDependentPluginTwo],
            [IsolatedDependentPluginOne, IsolatedDependentPluginTwo],
            [IsolatedDependentPluginOne, IsolatedDependentPluginTwo],
        ),
        (
            [DownStream, UpstreamAndDownstream, Upstream],
            [Upstream, UpstreamAndDownstream],
            [Upstream],
        ),
        (
            [DownStream, UpstreamAndDownstream, Upstream],
            [Upstream, UpstreamAndDownstream, DownStream],
            [Upstream, UpstreamAndDownstream, DownStream],
        ),
    ],
)
async def test_sort_dependent_plugin_graph(
    expected: list[type[_DummyDependentPlugin]],
    updated: list[type[_DummyDependentPlugin]],
    initial: Sequence[type[_DummyDependentPlugin]],
) -> None:
    sorter = TopologicalSorter[type[_DummyDependentPlugin]]()
    updated_entry_point_plugins = await sort_dependent_plugin_graph(
        sorter,
        StaticPluginRepository[_DummyDependentPlugin](
            DownStream,
            Upstream,
            UpstreamAndDownstream,
            IsolatedDependentPluginOne,
            IsolatedDependentPluginTwo,
        ),
        initial,
    )
    assert list(sorter.static_order()) == expected
    assert updated_entry_point_plugins == updated


class TestCyclicDependencyError:
    def test(self) -> None:
        sut = CyclicDependencyError([DummyPlugin])
        assert str(sut)
