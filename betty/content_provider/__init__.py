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
    from betty.document import Document


class ContentProvider(ABC, Plugin["ContentProviderDefinition"]):
    """
    A content provider.
    """

    @abstractmethod
    async def provide(self, *, document: Document) -> str | None:
        """
        Render the content.
        """


@final
@PluginTypeDefinition(
    "content-provider",
    base_cls=ContentProvider,
    label=_("Content provider"),
    label_plural=_("Content providers"),
    label_countable=ngettext("{count} content provider", "{count} content providers"),
    discovery=EntryPointDiscovery("betty.content_provider"),
)
class ContentProviderDefinition(HumanFacingPluginDefinition[ContentProvider]):
    """
    .. plugin_type:: content-provider.
    """
