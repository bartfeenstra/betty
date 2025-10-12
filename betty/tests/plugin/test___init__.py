from __future__ import annotations

from graphlib import TopologicalSorter
from typing import TYPE_CHECKING, TypeVar

import pytest
from typing_extensions import override

from betty.plugin import (
    CyclicDependencyError,
    DependentPlugin,
    OrderedPlugin,
    Plugin,
    PluginIdentifier,
    PluginIdToTypeMapping,
    PluginNotFound,
    PluginRepository,
    expand_plugin_dependencies,
    get_comes_after,
    get_comes_before,
    resolve_identifier,
    sort_dependent_plugin_graph,
    sort_ordered_plugin_graph,
)
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import DummyPlugin

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable

    from betty.machine_name import MachineName

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


class _TestPluginRepositoryPluginRepository(PluginRepository[DummyPlugin]):
    def __init__(self, *plugins: type[DummyPlugin]):
        super().__init__(DummyPlugin)
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
        await PluginIdToTypeMapping.new(StaticPluginRepository(DummyPlugin))

    async def test_get(self) -> None:
        sut = await PluginIdToTypeMapping.new(
            StaticPluginRepository(DummyPlugin, DummyPlugin)
        )
        assert sut.get(DummyPlugin.plugin_id()) is DummyPlugin

    async def test___getitem__(self) -> None:
        sut = await PluginIdToTypeMapping.new(
            StaticPluginRepository(DummyPlugin, DummyPlugin)
        )
        assert sut[DummyPlugin.plugin_id()] is DummyPlugin

    async def test___iter__(self) -> None:
        sut = await PluginIdToTypeMapping.new(
            StaticPluginRepository(DummyPlugin, DummyPlugin)
        )
        assert list(iter(sut)) == [DummyPlugin.plugin_id()]


class TestPluginRepository:
    async def test_plugin(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        assert sut.plugin is DummyPlugin

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

    async def test_plugin_id_schema(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginOne,
            _TestPluginRepositoryPluginOneTwo,
            _TestPluginRepositoryPluginOneTwoThree,
        )
        actual = await sut.plugin_id_schema
        assert actual.schema["enum"] == [
            "test-plugin-repository-plugin-one",
            "test-plugin-repository-plugin-one-two",
            "test-plugin-repository-plugin-one-two-three",
        ]


class TestCyclicDependencyError:
    def test(self) -> None:
        sut = CyclicDependencyError([DummyPlugin])
        assert str(sut)


class _DummyOrderedPlugin(OrderedPlugin["_DummyOrderedPlugin"], DummyPlugin):
    pass


class ComesBeforeTargetOrderedPlugin(_DummyOrderedPlugin):
    pass


class HasComesBeforeOrderedPlugin(_DummyOrderedPlugin):
    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[_DummyOrderedPlugin]]:
        return {ComesBeforeTargetOrderedPlugin}


class ComesAfterTargetOrderedPlugin(_DummyOrderedPlugin):
    pass


class HasComesAfterOrderedPlugin(_DummyOrderedPlugin):
    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[_DummyOrderedPlugin]]:
        return {ComesAfterTargetOrderedPlugin}


class IsolatedOrderedPlugin(_DummyOrderedPlugin):
    pass


@pytest.mark.parametrize(
    ("expected", "plugins"),
    [
        (
            [],
            [],
        ),
        (
            [IsolatedOrderedPlugin],
            [IsolatedOrderedPlugin],
        ),
        (
            [HasComesAfterOrderedPlugin],
            [HasComesAfterOrderedPlugin],
        ),
        (
            [ComesAfterTargetOrderedPlugin, HasComesAfterOrderedPlugin],
            [ComesAfterTargetOrderedPlugin, HasComesAfterOrderedPlugin],
        ),
        (
            [HasComesBeforeOrderedPlugin],
            [HasComesBeforeOrderedPlugin],
        ),
        (
            [HasComesBeforeOrderedPlugin, ComesBeforeTargetOrderedPlugin],
            [ComesBeforeTargetOrderedPlugin, HasComesBeforeOrderedPlugin],
        ),
    ],
)
async def test_sort_ordered_plugin_graph(
    expected: list[type[_DummyOrderedPlugin]],
    plugins: Iterable[type[_DummyOrderedPlugin]],
) -> None:
    sorter = TopologicalSorter[type[_DummyOrderedPlugin]]()
    await sort_ordered_plugin_graph(
        StaticPluginRepository(
            _DummyOrderedPlugin,
            ComesBeforeTargetOrderedPlugin,
            HasComesBeforeOrderedPlugin,
            ComesAfterTargetOrderedPlugin,
            HasComesAfterOrderedPlugin,
            IsolatedOrderedPlugin,
        ),
        plugins,
        sorter,
    )
    assert list(sorter.static_order()) == expected


class _DummyDependentPlugin(DependentPlugin["_DummyDependentPlugin"], DummyPlugin):
    pass


class DownStreamDependentPlugin(_DummyDependentPlugin):
    pass


class UpstreamDependentPlugin(_DummyDependentPlugin):
    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[_DummyDependentPlugin]]:
        return {UpstreamAndDownstreamDependentPlugin}


class UpstreamAndDownstreamDependentPlugin(_DummyDependentPlugin):
    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[_DummyDependentPlugin]]:
        return {DownStreamDependentPlugin}


class IsolatedDependentPlugin(_DummyDependentPlugin):
    pass


@pytest.mark.parametrize(
    ("expected", "plugins"),
    [
        (
            set(),
            set(),
        ),
        (
            {
                IsolatedDependentPlugin,
            },
            {
                IsolatedDependentPlugin,
            },
        ),
        (
            {
                DownStreamDependentPlugin,
                UpstreamAndDownstreamDependentPlugin,
                UpstreamDependentPlugin,
            },
            {
                UpstreamDependentPlugin,
                UpstreamAndDownstreamDependentPlugin,
                DownStreamDependentPlugin,
            },
        ),
        (
            {
                DownStreamDependentPlugin,
                UpstreamAndDownstreamDependentPlugin,
                UpstreamDependentPlugin,
            },
            {
                UpstreamDependentPlugin,
            },
        ),
        (
            {
                DownStreamDependentPlugin,
                UpstreamAndDownstreamDependentPlugin,
            },
            {
                UpstreamAndDownstreamDependentPlugin,
            },
        ),
        (
            {DownStreamDependentPlugin},
            {
                DownStreamDependentPlugin,
            },
        ),
    ],
)
async def test_expand_plugin_dependencies(
    expected: set[type[_DummyDependentPlugin]],
    plugins: set[type[_DummyDependentPlugin]],
) -> None:
    actual = await expand_plugin_dependencies(
        StaticPluginRepository(
            _DummyDependentPlugin,
            IsolatedDependentPlugin,
            UpstreamDependentPlugin,
            UpstreamAndDownstreamDependentPlugin,
            DownStreamDependentPlugin,
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
                IsolatedDependentPlugin,
            ],
            {
                IsolatedDependentPlugin,
            },
        ),
        (
            [
                DownStreamDependentPlugin,
                UpstreamAndDownstreamDependentPlugin,
                UpstreamDependentPlugin,
            ],
            {
                UpstreamDependentPlugin,
                UpstreamAndDownstreamDependentPlugin,
                DownStreamDependentPlugin,
            },
        ),
        (
            [
                DownStreamDependentPlugin,
                UpstreamAndDownstreamDependentPlugin,
                UpstreamDependentPlugin,
            ],
            {
                UpstreamDependentPlugin,
            },
        ),
        (
            [
                DownStreamDependentPlugin,
                UpstreamAndDownstreamDependentPlugin,
            ],
            {
                UpstreamAndDownstreamDependentPlugin,
            },
        ),
        (
            [DownStreamDependentPlugin],
            {
                DownStreamDependentPlugin,
            },
        ),
    ],
)
async def test_sort_dependent_plugin_graph(
    expected: list[type[DummyPlugin]], plugins: Iterable[type[_DummyDependentPlugin]]
) -> None:
    plugin_repository = StaticPluginRepository(
        _DummyDependentPlugin,
        IsolatedDependentPlugin,
        UpstreamDependentPlugin,
        UpstreamAndDownstreamDependentPlugin,
        DownStreamDependentPlugin,
    )
    sorter = TopologicalSorter[type[_DummyDependentPlugin]]()
    await sort_dependent_plugin_graph(plugin_repository, plugins, sorter)
    assert list(sorter.static_order()) == expected


class HasBidirectionalComesBeforeOrderedPlugin(_DummyOrderedPlugin):
    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[_DummyOrderedPlugin]]:
        return {HasBidirectionalComesAfterOrderedPlugin}


class HasBidirectionalComesAfterOrderedPlugin(_DummyOrderedPlugin):
    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[_DummyOrderedPlugin]]:
        return {HasBidirectionalComesBeforeOrderedPlugin}


@pytest.mark.parametrize(
    ("expected", "origin"),
    [
        (
            set(),
            IsolatedOrderedPlugin,
        ),
        (
            {ComesBeforeTargetOrderedPlugin},
            HasComesBeforeOrderedPlugin,
        ),
        (
            {HasComesAfterOrderedPlugin},
            ComesAfterTargetOrderedPlugin,
        ),
        (
            {HasBidirectionalComesAfterOrderedPlugin},
            HasBidirectionalComesBeforeOrderedPlugin,
        ),
    ],
)
async def test_get_comes_before(
    expected: set[type[_DummyOrderedPlugin]],
    origin: type[_DummyOrderedPlugin],
) -> None:
    assert (
        await get_comes_before(
            StaticPluginRepository(
                _DummyOrderedPlugin,
                ComesBeforeTargetOrderedPlugin,
                HasComesBeforeOrderedPlugin,
                ComesAfterTargetOrderedPlugin,
                HasComesAfterOrderedPlugin,
                IsolatedOrderedPlugin,
                HasBidirectionalComesBeforeOrderedPlugin,
                HasBidirectionalComesAfterOrderedPlugin,
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
            IsolatedOrderedPlugin,
        ),
        (
            {ComesAfterTargetOrderedPlugin},
            HasComesAfterOrderedPlugin,
        ),
        (
            {HasComesBeforeOrderedPlugin},
            ComesBeforeTargetOrderedPlugin,
        ),
        (
            {HasBidirectionalComesBeforeOrderedPlugin},
            HasBidirectionalComesAfterOrderedPlugin,
        ),
    ],
)
async def test_get_comes_after(
    expected: set[type[_DummyOrderedPlugin]],
    origin: type[_DummyOrderedPlugin],
) -> None:
    assert (
        await get_comes_after(
            StaticPluginRepository(
                _DummyOrderedPlugin,
                ComesAfterTargetOrderedPlugin,
                HasComesAfterOrderedPlugin,
                ComesBeforeTargetOrderedPlugin,
                HasComesBeforeOrderedPlugin,
                IsolatedOrderedPlugin,
                HasBidirectionalComesAfterOrderedPlugin,
                HasBidirectionalComesBeforeOrderedPlugin,
            ),
            origin,
        )
        == expected
    )
