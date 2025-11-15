"""
Content providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPluginDefinition,
    HumanFacingPluginDefinition,
    PluginTypeDefinition,
    ProjectPluginRepositoryDefinition,
)

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
class ContentProviderDefinition(
    HumanFacingPluginDefinition, ClassedPluginDefinition[ContentProvider]
):
    """
    A content provider definition.
    """

    plugin_type_cls = ContentProvider
    repository = ProjectPluginRepositoryDefinition(
        lambda project: project.content_provider_repository
    )
    type = PluginTypeDefinition(
        id="content-provider",
        label=_("Content provider"),
    )
