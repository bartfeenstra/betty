"""
Provide tools for proxying plugin management to other tools.
"""

from collections.abc import AsyncIterator
from typing import Generic, TypeVar

from typing_extensions import override

from betty.plugin import PluginRepository, Plugin, PluginNotFound, PluginId

_PluginT = TypeVar("_PluginT", bound=Plugin)


class ProxyPluginRepository(PluginRepository[_PluginT], Generic[_PluginT]):
    """
    Expose multiple other plugin repositories as one unified repository.
    """

    def __init__(self, *upstreams: PluginRepository[_PluginT]):
        self._upstreams = upstreams

    @override
    async def get(self, plugin_id: PluginId) -> type[_PluginT]:
        for upstream in self._upstreams:
            try:
                return await upstream.get(plugin_id)
            except PluginNotFound:
                pass
        raise PluginNotFound.new(plugin_id) from None

    @override
    async def __aiter__(self) -> AsyncIterator[type[_PluginT]]:
        seen = set()
        for upstream in self._upstreams:
            async for plugin in upstream:
                if plugin.plugin_id() not in seen:
                    seen.add(plugin.plugin_id())
                    yield plugin
