"""
Test utilities for :py:mod:`betty.content_provider`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.content_provider import ContentProvider, ContentProviderDefinition

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentProviderDefinition("no-op", label="No-op")
class NoOpContentProvider(ContentProvider):
    """
    A content provider that never provides any content.
    """

    @override
    async def provide(self, *, document: Document) -> str | None:
        return None
