"""
Discover plugins that are defined through an :py:class:`betty.project.extension.Extension`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, final

from typing_extensions import TypeVar, override

from betty.asyncio import ensure_await
from betty.plugin import PluginDefinition, PluginIdentifier, resolve_id
from betty.plugin.discovery import PluginDiscovery

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from betty.project.extension import Extension, ExtensionDefinition
    from betty.service_level import ServiceLevel


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class ExtensionDiscovery(
    PluginDiscovery[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    Discover plugins that are defined through an :py:class:`betty.project.extension.Extension`.
    """

    def __init__(
        self,
        extension: PluginIdentifier[ExtensionDefinition, Extension],
        discovery: Callable[[Extension], Awaitable[Iterable[_PluginDefinitionT]]]
        | Callable[[Extension], Iterable[_PluginDefinitionT]],
        /,
    ):
        self._extension_id = resolve_id(extension)
        self._discovery = discovery

    @override
    async def discover(
        self, service_level: ServiceLevel, /
    ) -> Iterable[_PluginDefinitionT]:
        from betty.project import Project

        if not isinstance(service_level, Project):
            return ()
        extensions = await service_level.extensions
        if self._extension_id not in extensions:
            return ()
        return await ensure_await(self._discovery(extensions[self._extension_id]))
