from collections.abc import Iterable

import pytest

from betty.machine_name import MachineName
from betty.plugin import Plugin
from betty.service.plugin import PluginCollection
from betty.test_utils.plugin import (
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

    async def test___contains____without_plugins(self) -> None:
        sut = PluginCollection([])
        assert DummyPluginOne not in sut

    async def test___contains____with_unknown_plugin(self) -> None:
        sut = PluginCollection([[]])
        assert DummyPluginOne not in sut

    async def test___contains____with_known_plugin(self) -> None:
        sut = PluginCollection([[self.PLUGIN_ONE]])
        assert DummyPluginOne in sut

    async def test___getitem____without_plugins(self) -> None:
        sut = PluginCollection([])
        with pytest.raises(KeyError):
            sut[DummyPluginOne]

    async def test___getitem____with_unknown_plugin(self) -> None:
        sut = PluginCollection([[]])
        with pytest.raises(KeyError):
            sut[DummyPluginOne]

    async def test___getitem____with_known_plugin(self) -> None:
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
    async def test___iter__(
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
