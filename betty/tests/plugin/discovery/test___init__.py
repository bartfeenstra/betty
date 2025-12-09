from __future__ import annotations

from betty.plugin.discovery import discover
from betty.plugin.discovery.static import StaticDiscovery
from betty.test_utils.plugin import DummyPluginOne


async def test_discover() -> None:
    assert DummyPluginOne.plugin() in await discover(
        None, StaticDiscovery(DummyPluginOne.plugin())
    )
