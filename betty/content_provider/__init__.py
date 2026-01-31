"""
Content providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.cls import PluginClsDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery

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
    label=_("Content provider"),
    label_plural=_("Content providers"),
    label_countable=ngettext("{count} content provider", "{count} content providers"),
    discovery=EntryPointDiscovery("betty.content_provider"),
)
class ContentProviderDefinition(
    HumanFacingDefinition, PluginClsDefinition[ContentProvider]
):
    """
    .. plugin_type:: content-provider.
    """
