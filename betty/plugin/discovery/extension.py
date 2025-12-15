"""
Discover plugins that are defined through an :py:class:`betty.project.extension.Extension`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar, override

from betty.asyncio import ensure_await
from betty.plugin import PluginDefinition
from betty.plugin.discovery import PluginDiscovery
from betty.plugin.resolve import ResolvableId, resolve_id

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from betty.project.extension import Extension, ExtensionDefinition
    from betty.service.level import ServiceLevel


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class ExtensionDiscovery(PluginDiscovery[_PluginDefinitionT]):
    """
    Discover plugins that are defined through an :py:class:`betty.project.extension.Extension`.
    """

    def __init__(
        self,
        extension: ResolvableId[ExtensionDefinition],
        discovery: Callable[[Extension], Awaitable[Iterable[_PluginDefinitionT]]]
        | Callable[[Extension], Iterable[_PluginDefinitionT]],
        /,
    ):
        self._extension_id = resolve_id(extension)
        self._discovery = discovery

    @override
    async def discover(self, services: ServiceLevel, /) -> Iterable[_PluginDefinitionT]:
        from betty.project import Project

        if not isinstance(services, Project):
            return ()
        extensions = await services.extensions
        if self._extension_id not in extensions:
            return ()
        return await ensure_await(self._discovery(extensions[self._extension_id]))
