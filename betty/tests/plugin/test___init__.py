from __future__ import annotations

from graphlib import TopologicalSorter
from typing import Self, Literal, TYPE_CHECKING, TypeVar

import pytest
from typing_extensions import override

from betty.factory import Factory, new
from betty.plugin import (
    PluginNotFound,
    Plugin,
    PluginRepository,
    PluginIdToTypeMap,
    sort_ordered_plugin_graph,
    PluginIdentifier,
    OrderedPlugin,
    DependentPlugin,
    sort_dependent_plugin_graph,
    CyclicDependencyError,
)
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import DummyPlugin

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from collections.abc import AsyncIterator, Sequence


_T = TypeVar("_T")


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
    def __init__(self, *plugins: type[DummyPlugin], factory: Factory | None = None):
        super().__init__(factory=factory)
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


class TestPluginIdToTypeMap:
    async def test_new(self) -> None:
        await PluginIdToTypeMap.new(StaticPluginRepository())

    async def test_get(self) -> None:
        sut = await PluginIdToTypeMap.new(StaticPluginRepository(DummyPlugin))
        assert sut.get(DummyPlugin.plugin_id()) is DummyPlugin

    async def test___getitem__(self) -> None:
        sut = await PluginIdToTypeMap.new(StaticPluginRepository(DummyPlugin))
        assert sut[DummyPlugin.plugin_id()] is DummyPlugin


class TestPluginRepository:
    async def test_resolve_identifier_with_unknown_plugin_id(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        with pytest.raises(PluginNotFound):
            await sut.resolve_identifier("unknown-plugin")

    async def test_resolve_identifier_with_known_plugin_id(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(_TestPluginRepositoryPluginOne)
        assert (
            await sut.resolve_identifier(_TestPluginRepositoryPluginOne.plugin_id())
            == _TestPluginRepositoryPluginOne
        )

    async def test_resolve_identifier_with_known_plugin(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(_TestPluginRepositoryPluginOne)
        assert (
            await sut.resolve_identifier(_TestPluginRepositoryPluginOne)
            is _TestPluginRepositoryPluginOne
        )

    async def test_resolve_identifiers_without_identifiers(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        assert await sut.resolve_identifiers([]) == []

    async def test_resolve_identifiers_with_unknown_plugin_id(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        with pytest.raises(PluginNotFound):
            await sut.resolve_identifiers(["unknown-plugin"])

    async def test_resolve_identifiers_with_known_plugin_id(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(_TestPluginRepositoryPluginOne)
        assert await sut.resolve_identifiers(
            [_TestPluginRepositoryPluginOne.plugin_id()]
        ) == [_TestPluginRepositoryPluginOne]

    async def test_resolve_identifiers_with_known_plugin(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(_TestPluginRepositoryPluginOne)
        assert await sut.resolve_identifiers([_TestPluginRepositoryPluginOne]) == [
            _TestPluginRepositoryPluginOne
        ]

    async def test_map_without_plugins(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        await sut.map()

    async def test_map_with_plugins(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginOne,
            _TestPluginRepositoryPluginOneTwo,
            _TestPluginRepositoryPluginOneTwoThree,
        )
        plugin_id_to_type_map = await sut.map()
        assert (
            plugin_id_to_type_map[_TestPluginRepositoryPluginOne.plugin_id()]
            is _TestPluginRepositoryPluginOne
        )

    async def test_select_without_plugins(self) -> None:
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
    async def test_select_with_mixins(
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

    async def test_new_target_with_default_factory(self) -> None:
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

    async def test_new_target_with_custom_factory(self) -> None:
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


class TestSortOrderedPluginGraph:
    _PLUGINS = StaticPluginRepository[_DummyOrderedPlugin](
        ComesBeforeTargetPlugin,
        HasComesBeforePlugin,
        ComesAfterTargetPlugin,
        HasComesAfterPlugin,
        IsolatedOrderedPluginOne,
        IsolatedOrderedPluginTwo,
    )

    async def test_without_entry_point_plugins(self) -> None:
        sorter = TopologicalSorter[type[_DummyOrderedPlugin]]()
        await sort_ordered_plugin_graph(sorter, self._PLUGINS, [])
        assert list(sorter.static_order()) == []

    async def test_with_isolated_entry_point_plugins(self) -> None:
        sorter = TopologicalSorter[type[_DummyOrderedPlugin]]()
        await sort_ordered_plugin_graph(
            sorter, self._PLUGINS, [IsolatedOrderedPluginOne, IsolatedOrderedPluginTwo]
        )
        assert list(sorter.static_order()) == [
            IsolatedOrderedPluginOne,
            IsolatedOrderedPluginTwo,
        ]

    async def test_with_unknown_comes_after(self) -> None:
        plugins = {HasComesAfterPlugin}
        sorter = TopologicalSorter[type[_DummyOrderedPlugin]]()
        await sort_ordered_plugin_graph(sorter, self._PLUGINS, plugins)
        assert list(sorter.static_order()) == [HasComesAfterPlugin]

    async def test_with_known_comes_after(self) -> None:
        plugins = {ComesAfterTargetPlugin, HasComesAfterPlugin}
        sorter = TopologicalSorter[type[_DummyOrderedPlugin]]()
        await sort_ordered_plugin_graph(sorter, self._PLUGINS, plugins)
        assert list(sorter.static_order()) == [
            ComesAfterTargetPlugin,
            HasComesAfterPlugin,
        ]

    async def test_with_unknown_comes_before(self) -> None:
        sorter = TopologicalSorter[type[_DummyOrderedPlugin]]()
        await sort_ordered_plugin_graph(sorter, self._PLUGINS, [HasComesBeforePlugin])
        assert list(sorter.static_order()) == [HasComesBeforePlugin]

    async def test_with_known_comes_before(self) -> None:
        sorter = TopologicalSorter[type[_DummyOrderedPlugin]]()
        await sort_ordered_plugin_graph(
            sorter, self._PLUGINS, [ComesBeforeTargetPlugin, HasComesBeforePlugin]
        )
        assert list(sorter.static_order()) == [
            HasComesBeforePlugin,
            ComesBeforeTargetPlugin,
        ]


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


class TestSortDependentPluginGraph:
    _PLUGINS = StaticPluginRepository[_DummyDependentPlugin](
        DownStream,
        Upstream,
        UpstreamAndDownstream,
        IsolatedDependentPluginOne,
        IsolatedDependentPluginTwo,
    )

    async def test_without_entry_point_plugins(self) -> None:
        sorter = TopologicalSorter[type[_DummyDependentPlugin]]()
        await sort_dependent_plugin_graph(sorter, self._PLUGINS, [])
        assert list(sorter.static_order()) == []

    async def test_with_isolated_entry_point_plugins(self) -> None:
        sorter = TopologicalSorter[type[_DummyDependentPlugin]]()
        await sort_dependent_plugin_graph(
            sorter,
            self._PLUGINS,
            [IsolatedDependentPluginOne, IsolatedDependentPluginTwo],
        )
        assert list(sorter.static_order()) == [
            IsolatedDependentPluginOne,
            IsolatedDependentPluginTwo,
        ]

    async def test_with_unknown_dependencies(self) -> None:
        sorter = TopologicalSorter[type[_DummyDependentPlugin]]()
        await sort_dependent_plugin_graph(sorter, self._PLUGINS, [Upstream])
        assert list(sorter.static_order()) == [
            DownStream,
            UpstreamAndDownstream,
            Upstream,
        ]

    async def test_with_known_dependencies(self) -> None:
        sorter = TopologicalSorter[type[_DummyDependentPlugin]]()
        await sort_dependent_plugin_graph(
            sorter, self._PLUGINS, [Upstream, UpstreamAndDownstream, DownStream]
        )
        assert list(sorter.static_order()) == [
            DownStream,
            UpstreamAndDownstream,
            Upstream,
        ]


class TestCyclicDependencyError:
    def test(self) -> None:
        sut = CyclicDependencyError([DummyPlugin])
        assert str(sut)
