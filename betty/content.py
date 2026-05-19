"""
Content plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from markupsafe import Markup

from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document
    from betty.locale.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


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
class ContentDefinition(HumanFacingDefinition, PluginClsDefinition[Content]):
    """
    .. plugin_type:: content.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        auto: bool = False,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            auto=auto,
            label=label,
            description=description,
            requires=requires,
        )


@final
@PluginManufacturerDefinition(ContentDefinition)
class ContentManufacturer(PluginManufacturer[ContentDefinition, Content]):
    """
    The content manufacturer.
    """


async def build(document: Document, contents: Iterable[Content], /) -> Markup | None:
    """
    Build content for the given document and contents.
    """
    built = "".join([
        await content.build(document=document) or "" for content in contents
    ]).strip()
    if built:
        return Markup(built)
    return None
