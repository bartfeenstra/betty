from __future__ import annotations

from importlib.metadata import EntryPoint, EntryPoints
from typing import TYPE_CHECKING

from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.service.level import universe
from betty.test_utils.plugin import DummyPluginOne, DummyPluginTwo

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestEntryPointDiscovery:
    async def test_discover(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=DummyPluginOne.plugin().id,
                        value="betty.test_utils.plugin:DummyPluginOne",
                        group=entry_point_group,
                    ),
                    EntryPoint(
                        name=DummyPluginTwo.plugin().id,
                        value="betty.test_utils.plugin:DummyPluginTwo",
                        group=entry_point_group,
                    ),
                ]
            ),
        )
        sut = EntryPointDiscovery(entry_point_group)
        plugins = await sut.discover(services=universe)
        assert DummyPluginOne in plugins
        assert DummyPluginTwo in plugins
        m_entry_points.assert_called_once_with(group=entry_point_group)
