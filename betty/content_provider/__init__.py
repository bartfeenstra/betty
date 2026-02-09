"""
Content providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from markupsafe import Markup

from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery

if TYPE_CHECKING:
    from collections.abc import Iterable

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
    discovery=[EntryPointDiscovery("betty.content_provider")],
)
class ContentProviderDefinition(
    HumanFacingDefinition, PluginDefinition[ContentProvider]
):
    """
    .. plugin_type:: content-provider.
    """


async def provide_content(
    document: Document, contents: Iterable[ContentProvider], /
) -> Markup | None:
    """
    Provided content for the given document and content providers.
    """
    provided = "".join(
        [await content.provide(document=document) or "" for content in contents]
    ).strip()
    if provided:
        return Markup(provided)
    return None
