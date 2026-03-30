"""
Content plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final, override

from markupsafe import Markup

from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer
from betty.service.plugin.service import ServicePluginDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document


class Content(ABC, Plugin["ContentDefinition"]):
    """
    A content plugin.
    """

    @abstractmethod
    async def build(self, *, document: Document) -> str | None:
        """
        Render the content.
        """


@final
@PluginTypeDefinition(
    "content",
    label=_("Content"),
    label_plural=_("Contents"),
    label_countable=ngettext("{count} content", "{count} contents"),
)
class ContentDefinition(HumanFacingDefinition, ServicePluginDefinition[Content]):
    """
    .. plugin_type:: content.
    """


@final
class ContentManufacturer(PluginManufacturer[ContentDefinition, Content]):
    """
    The content manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[ContentDefinition]:
        return ContentDefinition


async def build(document: Document, contents: Iterable[Content], /) -> Markup | None:
    """
    Build content for the given document and contents.
    """
    built = "".join(
        [await content.build(document=document) or "" for content in contents]
    ).strip()
    if built:
        return Markup(built)
    return None
