from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.plugin.error import PluginNotFound
from betty.plugin.repository import PluginRepository
from betty.test_utils.plugin import (
    DummyPluginDefinition,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from betty.machine_name import MachineName


class TestPluginRepository:
    class _Sut(PluginRepository[DummyPluginDefinition]):
        def __init__(self, *plugins: DummyPluginDefinition):
            super().__init__(DummyPluginDefinition)
            self._plugins = {plugin.id: plugin for plugin in plugins}

        @override
        async def plugin(self, plugin_id: MachineName, /) -> DummyPluginDefinition:
            try:
                return self._plugins[plugin_id]
            except KeyError:
                raise PluginNotFound(
                    DummyPluginDefinition.type(), plugin_id, []
                ) from None

        @override
        async def __aiter__(self) -> AsyncIterator[DummyPluginDefinition]:
            for plugin in self._plugins.values():
                yield plugin

    def test_type(self) -> None:
        assert self._Sut().type is DummyPluginDefinition
