"""
Test utilities for :py:mod:`betty.content_provider`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase

if TYPE_CHECKING:
    from betty.document import Document


class ContentProviderDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.content_provider.ContentProviderDefinition` implementations.
    """


class ContentProviderTestBase(PluginTestBase[ContentProvider]):
    """
    A base class for testing :py:class:`betty.content_provider.ContentProvider` implementations.
    """


@final
@ContentProviderDefinition("no-op", label="No-op")
class NoOpContentProvider(ContentProvider):
    """
    A content provider that never provides any content.
    """

    @override
    async def provide(self, *, document: Document) -> str | None:
        return None
