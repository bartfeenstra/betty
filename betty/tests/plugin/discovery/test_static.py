from __future__ import annotations

from betty.plugin.discovery.static import StaticDiscovery
from betty.test_utils.plugin import DummyPluginOne


class TestStaticDiscovery:
    async def test_discover(self) -> None:
        sut = StaticDiscovery(DummyPluginOne)
        plugins = await sut.discover(None)
        assert DummyPluginOne.plugin() in plugins
