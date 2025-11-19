from __future__ import annotations

from betty.plugin.discovery import discover
from betty.plugin.discovery.static import StaticDiscovery
from betty.test_utils.plugin import DUMMY_PLUGIN_ONE


async def test_discover() -> None:
    assert DUMMY_PLUGIN_ONE in await discover(None, StaticDiscovery(DUMMY_PLUGIN_ONE))
