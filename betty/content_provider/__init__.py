"""
Content providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    HumanFacingPluginDefinition,
)

if TYPE_CHECKING:
    from betty.job import Context


class ContentProvider(ABC):
    """
    A content provider.
    """

    @abstractmethod
    async def provide(
        self, *, locale: str, page_resource: Any, job_context: Context | None = None
    ) -> str | None:
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

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="content-provider",
        label=_("Content provider"),
        cls=ContentProvider,
    )
