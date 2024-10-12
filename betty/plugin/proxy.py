"""
Provide tools for proxying plugin management to other tools.
"""

from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Generic, TypeVar, final

from typing_extensions import override

from betty.factory import Factory, FactoryError
from betty.machine_name import MachineName
from betty.plugin import PluginRepository, Plugin, PluginNotFound, PluginIdentifier

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
    async def new_target(self, cls: PluginIdentifier[_PluginT]) -> _PluginT:
        with suppress(FactoryError):
            return await super().new_target(cls)
        if isinstance(cls, str):
            cls = await self.get(cls)
        for upstream in self._upstreams:
            with suppress(PluginNotFound, FactoryError):
                await upstream.get(cls.plugin_id())
                return await upstream.new_target(cls)
        raise FactoryError()

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
