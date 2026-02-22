"""
Test utilities for :py:mod:`betty.content`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.content import Content, ContentDefinition

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition("no-op", label="No-op")
class NoOpContent(Content):
    """
    A content plugin that never provides any content.
    """

    @override
    async def build(self, *, document: Document) -> str | None:
        return None
