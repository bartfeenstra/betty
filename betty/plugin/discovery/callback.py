"""
Discover plugins using your own callbacks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from typing_extensions import TypeVar, override

from betty.asyncio import ensure_await
from betty.plugin import PluginDefinition
from betty.plugin.discovery import PluginDiscovery

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from betty.service_level import ServiceLevel

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class CallbackDiscovery(
    PluginDiscovery[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    Discover plugins using your own callbacks.
    """

    def __init__(
        self,
        discovery: Callable[[], Awaitable[Iterable[_PluginDefinitionT]]]
        | Callable[[], Iterable[_PluginDefinitionT]],
        /,
    ):
        self._discovery = discovery

    @override
    async def discover(
        self, service_level: ServiceLevel, /
    ) -> Iterable[_PluginDefinitionT]:
        return await ensure_await(self._discovery())
