"""
Provide tools for proxying plugin management to other tools.
"""

from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Generic, TypeVar, final, overload

from typing_extensions import override

from betty.factory import Factory, FactoryError
from betty.json.schema import Schema
from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginNotFound, PluginRepository

_T = TypeVar("_T")
_PluginT = TypeVar("_PluginT", bound=Plugin)


@final
class ProxyPluginRepository(PluginRepository[_PluginT], Generic[_PluginT]):
    """
    Expose multiple other plugin repositories as one unified repository.
    """

    def __init__(
        self,
        *upstreams: PluginRepository[_PluginT],
        factory: Factory | None = None,
        schema_template: Schema | None = None,
    ):
        super().__init__(factory=factory, schema_template=schema_template)
        self._upstreams = upstreams

    @overload
    async def new_target(self, cls: type[_T]) -> _T:
        pass

    @overload
    async def new_target(self, cls: MachineName) -> _PluginT:
        pass

    @override
    async def new_target(self, cls: type[_T] | MachineName) -> _T | _PluginT:
        with suppress(FactoryError):
            return await super().new_target(cls)
        resolved_cls = await self.get(cls) if isinstance(cls, str) else cls
        for upstream in self._upstreams:
            if issubclass(resolved_cls, Plugin):
                try:
                    await upstream.get(resolved_cls.plugin_id())
                except PluginNotFound:
                    continue
            with suppress(PluginNotFound, FactoryError):
                return await upstream.new_target(resolved_cls)
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
