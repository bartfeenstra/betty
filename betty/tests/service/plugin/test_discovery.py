from collections.abc import Iterator
from importlib.metadata import EntryPoint, EntryPoints

import pytest
from pytest_mock import MockerFixture

from betty.importlib import fully_qualified_name
from betty.plugin.error import PluginNotFound
from betty.service.plugin.discovery import PluginDiscoverer
from betty.string import kebab_case_to_snake_case
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne
from betty.universe import UNIVERSE


class TestPluginDiscoverer:
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
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition, [])
        assert not [x async for x in aiter(sut)]

    async def test___aiter____with_discovered_plugins(self, entry_points: None) -> None:
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition)
        assert DummyPluginOne.plugin() in [x async for x in aiter(sut)]

    async def test___aiter____with_overridden_plugins(self) -> None:
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition, [DummyPluginOne])
        assert [x async for x in aiter(sut)] == [DummyPluginOne.plugin()]

    async def test___getitem____with_plugin_not_found(self) -> None:
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition, [])
        with pytest.raises(PluginNotFound):
            await sut["unknown-plugin"]

    async def test___getitem____with_discovered_plugins(
        self, entry_points: None
    ) -> None:
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition)
        assert await sut[DummyPluginOne.plugin().id] is DummyPluginOne.plugin()

    async def test___getitem____with_overridden_plugin(self) -> None:
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition, [DummyPluginOne])
        assert await sut[DummyPluginOne.plugin().id] is DummyPluginOne.plugin()

    async def test_ids__without_plugins(self) -> None:
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition, [])
        assert not list(await sut.ids())

    async def test_ids__with_discovered_plugins(self, entry_points: None) -> None:
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition)
        assert DummyPluginOne.plugin().id in list(await sut.ids())

    async def test_ids__with_overridden_plugins(self) -> None:
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition, [DummyPluginOne])
        assert list(await sut.ids()) == [DummyPluginOne.plugin().id]

    def test_type(self) -> None:
        sut = PluginDiscoverer(UNIVERSE, DummyPluginDefinition)
        assert sut.type is DummyPluginDefinition
