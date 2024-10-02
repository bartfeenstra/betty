"""
Provide tools for proxying plugin management to other tools.
"""

from collections.abc import AsyncIterator
from typing import Generic, TypeVar, final

from typing_extensions import override

from betty.factory import Factory
from betty.machine_name import MachineName
from betty.plugin import PluginRepository, Plugin, PluginNotFound

_PluginT = TypeVar("_PluginT", bound=Plugin)


@final
class ProxyPluginRepository(PluginRepository[_PluginT], Generic[_PluginT]):
    """
    Expose multiple other plugin repositories as one unified repository.
    """

    def __init__(
        self,
        *upstreams: PluginRepository[_PluginT],
        factory: Factory[_PluginT] | None = None,
    ):
        super().__init__(factory=factory)
        self._upstreams = upstreams

    @override
    async def get(self, plugin_id: MachineName) -> type[_PluginT]:
        for upstream in self._upstreams:
            try:
                return await upstream.get(plugin_id)
            except PluginNotFound:
                pass
        raise PluginNotFound.new(plugin_id, await self.select()) from None

    @override
    async def __aiter__(self) -> AsyncIterator[type[_PluginT]]:
        seen = set()
        for upstream in self._upstreams:
            async for plugin in upstream:
                if plugin.plugin_id() not in seen:
                    seen.add(plugin.plugin_id())
                    yield plugin
