"""
Content providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.locale.localizable import _
from betty.plugin import PluginTypeDefinition
from betty.plugin.classed import ClassedPluginDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition

if TYPE_CHECKING:
    from betty.resource import Context


class ContentProvider(ABC):
    """
    A content provider.
    """

    @abstractmethod
    async def provide(self, *, resource: Context) -> str | None:
        """
        Render the content.
        """


@final
class ContentProviderPlugin(
    HumanFacingPluginDefinition, ClassedPluginDefinition[ContentProvider]
):
    """
    A content provider definition.
    """

    plugin_type_cls = ContentProvider
    type = PluginTypeDefinition(
        id="content-provider",
        label=_("Content provider"),
        discoveries=EntryPointDiscovery("betty.content_provider"),
    )
