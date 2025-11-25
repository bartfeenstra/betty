"""
Discover plugins that are defined through an :py:class:`betty.app.App`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar, override

from betty.asyncio import ensure_await
from betty.plugin import PluginDefinition
from betty.plugin.discovery import PluginDiscovery
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from betty.app import App
    from betty.service.level import ServiceLevel


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
@internal
class AppDiscovery(PluginDiscovery[_PluginDefinitionT]):
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
    async def discover(self, services: ServiceLevel, /) -> Iterable[_PluginDefinitionT]:
        from betty.project import Project

        if services is None:
            return ()
        if isinstance(services, Project):
            services = services.app
        return await ensure_await(self._discovery(services))
