from __future__ import annotations

from betty.plugin.discovery.static import StaticDiscovery
from betty.service.level.universal import universe
from betty.test_utils.plugin import DummyPluginOne


class TestStaticDiscovery:
    async def test_discover(self) -> None:
        sut = StaticDiscovery(DummyPluginOne)
        plugins = await sut.discover(universe)
        assert DummyPluginOne.plugin() in plugins
