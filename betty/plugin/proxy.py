"""
Provide tools for proxying plugin management to other tools.
"""

from collections.abc import AsyncIterator
from typing import Generic, TypeVar, final

from typing_extensions import override

from betty.machine_name import MachineName
from betty.plugin import (
    PluginDefinition,
    PluginNotFound,
    PluginRepository,
)

_T = TypeVar("_T")
_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


@final
class ProxyPluginRepository(
    PluginRepository[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    Expose multiple other plugin repositories as one unified repository.
    """

    def __init__(
        self,
        plugin: type[_PluginDefinitionT],  # noqa A002
        *upstreams: PluginRepository[_PluginDefinitionT],
    ):
        super().__init__(plugin)
        self._upstreams = upstreams

    @override
    async def get(self, plugin_id: MachineName) -> _PluginDefinitionT:
        for upstream in self._upstreams:
            try:
                return await upstream.get(plugin_id)
            except PluginNotFound:
                pass
        raise PluginNotFound.new(plugin_id, [plugin async for plugin in self]) from None

    @override
    async def __aiter__(self) -> AsyncIterator[_PluginDefinitionT]:
        seen = set()
        for upstream in self._upstreams:
            async for plugin in upstream:
                if plugin.id not in seen:
                    seen.add(plugin.id)
                    yield plugin
