"""
Discover plugins that are defined through an :py:class:`betty.app.App`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from typing_extensions import TypeVar, override

from betty.asyncio import ensure_await
from betty.plugin import PluginDefinition
from betty.plugin.discovery import PluginDiscovery
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from betty.app import App
    from betty.service_level import ServiceLevel


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
@internal
class AppDiscovery(PluginDiscovery[_PluginDefinitionT], Generic[_PluginDefinitionT]):
    """
    Discover plugins that are defined through an :py:class:`betty.app.App`.
    """

    def __init__(
        self,
        discovery: Callable[[App], Awaitable[Iterable[_PluginDefinitionT]]]
        | Callable[[App], Iterable[_PluginDefinitionT]],
        /,
    ):
        self._discovery = discovery

    @override
    async def discover(
        self, service_level: ServiceLevel, /
    ) -> Iterable[_PluginDefinitionT]:
        from betty.project import Project

        if service_level is None:
            return ()
        if isinstance(service_level, Project):
            service_level = service_level.app
        return await ensure_await(self._discovery(service_level))
