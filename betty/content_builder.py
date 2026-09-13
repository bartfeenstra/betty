"""
The content builder API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, final

from markupsafe import Markup

from betty.definition.human_facing import HumanFacingDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import (
    NewPlugin,
    Plugin,
    ResolvablePluginManufacturer,
)
from betty.plugin.config import ConfigurablePluginDefinition
from betty.plugin.factory import NewPluginDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.data import Data
    from betty.document import Document
    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class ContentBuilder(Plugin["ContentBuilderDefinition"], metaclass=ABCMeta):
    """
    A content builder plugin.
    """

    @abstractmethod
    async def build(self, *, document: Document) -> str | None:
        """
        Render the content.
        """


@final
@PluginTypeDefinition(
    "content-builder",
    label=_("Content builder"),
    label_plural=_("Content builders"),
    label_countable=ngettext("{count} content builder", "{count} content builders"),
)
class ContentBuilderDefinition(
    HumanFacingDefinition, ConfigurablePluginDefinition[ContentBuilder]
):
    """
    .. plugin_type:: content-builder.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        config_cls: type[Data] | None = None,
        auto: bool = False,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            auto=auto,
            config_cls=config_cls,
            description=description,
            label=label,
            requires=requires,
        )


@final
@NewPluginDefinition(ContentBuilderDefinition)
class NewContentBuilder(NewPlugin[ContentBuilderDefinition, ContentBuilder]):
    """
    The content builder factory.
    """


type ResolvableContentBuilderManufacturer = ResolvablePluginManufacturer[
    ContentBuilderDefinition, NewContentBuilder
]


async def build(
    document: Document, contents: Iterable[ContentBuilder], /
) -> Markup | None:
    """
    Build content for the given document and contents.
    """
    built = "".join([
        await content.build(document=document) or "" for content in contents
    ]).strip()
    if built:
        return Markup(built)
    return None
