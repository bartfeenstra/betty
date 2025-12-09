"""
Content providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition

if TYPE_CHECKING:
    from betty.resource import Context


class ContentProvider(ABC, Plugin["ContentProviderDefinition"]):
    """
    A content provider.
    """

    @abstractmethod
    async def provide(self, *, resource: Context) -> str | None:
        """
        Render the content.
        """


@final
@PluginTypeDefinition(
    "content-provider",
    ContentProvider,
    _("Content provider"),
    _("Content providers"),
    ngettext("{count} content provider", "{count} content providers"),
    discovery=EntryPointDiscovery("betty.content_provider"),
)
class ContentProviderDefinition(HumanFacingPluginDefinition[ContentProvider]):
    """
    A content provider definition.
    """
