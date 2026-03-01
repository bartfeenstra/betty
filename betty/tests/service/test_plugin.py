from collections.abc import Iterable, Iterator
from importlib.metadata import EntryPoint, EntryPoints

import pytest
from pytest_mock import MockerFixture

from betty.importlib import fully_qualified_name
from betty.machine_name import MachineName
from betty.plugin import Plugin
from betty.plugin.error import PluginNotFound
from betty.service.level import UNIVERSE
from betty.service.plugin import PluginCollection, PluginManager
from betty.string import kebab_case_to_snake_case
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginFour,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)


class TestPluginCollection:
    PLUGIN_ONE = DummyPluginOne()
    PLUGIN_TWO = DummyPluginTwo()
    PLUGIN_THREE = DummyPluginThree()
    PLUGIN_FOUR = DummyPluginFour()

    def test___contains____without_plugins(self) -> None:
        sut = PluginCollection([])
        assert DummyPluginOne not in sut

    def test___contains____with_unknown_plugin(self) -> None:
        sut = PluginCollection([[]])
        assert DummyPluginOne not in sut

    def test___contains____with_known_plugin(self) -> None:
        sut = PluginCollection([[self.PLUGIN_ONE]])
        assert DummyPluginOne in sut

    def test___contains____with_invalid_value(self) -> None:
        sut = PluginCollection([])
        assert object() not in sut

    def test___getitem____without_plugins(self) -> None:
        sut = PluginCollection([])
        with pytest.raises(KeyError):
            sut[DummyPluginOne]

    def test___getitem____with_unknown_plugin(self) -> None:
        sut = PluginCollection([[]])
        with pytest.raises(KeyError):
            sut[DummyPluginOne]

    def test___getitem____with_known_plugin(self) -> None:
        sut = PluginCollection([[DummyPluginOne()]])
        sut[DummyPluginOne]

    @pytest.mark.parametrize(
        ("expected", "plugins"),
        [
            ([], []),
            ([PLUGIN_ONE], [[PLUGIN_ONE]]),
            (
                [
                    PLUGIN_ONE,
                    PLUGIN_TWO,
                    PLUGIN_THREE,
                    PLUGIN_FOUR,
                ],
                [
                    [PLUGIN_ONE, PLUGIN_TWO],
                    [PLUGIN_THREE, PLUGIN_FOUR],
                ],
            ),
        ],
    )
    def test___iter__(
        self, expected: list[Plugin], plugins: Iterable[Iterable[Plugin]]
    ) -> None:
        assert list(iter(PluginCollection(plugins))) == expected

    @pytest.mark.parametrize(
        ("expected", "plugins"),
        [
            (0, []),
            (1, [[DummyPluginOne()]]),
            (
                4,
                [
                    [DummyPluginOne(), DummyPluginTwo()],
                    [DummyPluginThree(), DummyPluginFour()],
                ],
            ),
        ],
    )
    def test___len__(self, expected: int, plugins: Iterable[Iterable[Plugin]]) -> None:
        assert len(PluginCollection(plugins)) == expected

    @pytest.mark.parametrize(
        ("expected", "plugins"),
        [
            ([], []),
            ([DummyPluginOne.plugin().id], [[DummyPluginOne()]]),
            (
                [
                    DummyPluginOne.plugin().id,
                    DummyPluginTwo.plugin().id,
                    DummyPluginThree.plugin().id,
                    DummyPluginFour.plugin().id,
                ],
                [
                    [DummyPluginOne(), DummyPluginTwo()],
                    [DummyPluginThree(), DummyPluginFour()],
                ],
            ),
        ],
    )
    def test_keys(
        self, expected: list[MachineName], plugins: Iterable[Iterable[Plugin]]
    ) -> None:
        assert list(PluginCollection(plugins).keys()) == expected


class TestPluginManager:
    @pytest.fixture
    def entry_points(self, mocker: MockerFixture) -> Iterator[None]:
        entry_point_group = kebab_case_to_snake_case(DummyPluginDefinition.type().id)
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=DummyPluginOne.plugin().id,
                        value=fully_qualified_name(DummyPluginOne),
                        group=entry_point_group,
                    ),
                ]
            ),
        )
        yield
        m_entry_points.assert_called_once_with(group=f"betty.{entry_point_group}")

    async def test___aiter____without_plugins(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [])
        assert not [x async for x in aiter(sut)]

    async def test___aiter____with_discovered_plugins(self, entry_points: None) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition)
        assert DummyPluginOne.plugin() in [x async for x in aiter(sut)]

    async def test___aiter____with_overridden_plugins(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [DummyPluginOne])
        assert [x async for x in aiter(sut)] == [DummyPluginOne.plugin()]

    async def test___getitem____with_plugin_not_found(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [])
        with pytest.raises(PluginNotFound):
            await sut["unknown-plugin"]

    async def test___getitem____with_discovered_plugins(
        self, entry_points: None
    ) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition)
        assert await sut[DummyPluginOne.plugin().id] is DummyPluginOne.plugin()

    async def test___getitem____with_overridden_plugin(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [DummyPluginOne])
        assert await sut[DummyPluginOne.plugin().id] is DummyPluginOne.plugin()

    async def test_ids__without_plugins(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [])
        assert not list(await sut.ids())

    async def test_ids__with_discovered_plugins(self, entry_points: None) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition)
        assert DummyPluginOne.plugin().id in list(await sut.ids())

    async def test_ids__with_overridden_plugins(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [DummyPluginOne])
        assert list(await sut.ids()) == [DummyPluginOne.plugin().id]

    def test_type(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition)
        assert sut.type is DummyPluginDefinition
