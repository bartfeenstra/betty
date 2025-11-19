from __future__ import annotations

from betty.plugin.discovery.static import StaticDiscovery
from betty.test_utils.plugin import DUMMY_PLUGIN_ONE


class TestStaticDiscovery:
    async def test_discover(self) -> None:
        sut = StaticDiscovery(DUMMY_PLUGIN_ONE)
        plugins = await sut.discover(None)
        assert DUMMY_PLUGIN_ONE in plugins
