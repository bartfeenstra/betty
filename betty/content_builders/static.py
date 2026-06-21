"""
Static content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.content_builder import ContentBuilder, ContentBuilderDefinition
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentBuilderDefinition("static", label=_("Static content"))
class Static(ContentBuilder):
    """
    .. plugin:: content-builder:static.
    """

    def __init__(self, content: str | None = None, /):
        self._content = content

    @override
    async def build(self, *, document: Document) -> str | None:
        return self._content
