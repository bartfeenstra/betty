"""
Static content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.content import Content, ContentDefinition
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from betty.document import Document


@final
@ContentDefinition("static", label=_("Static content"))
class Static(Content):
    """
    .. plugin:: content:static.
    """

    def __init__(self, content: str | None = None, /):
        self._content = content

    @override
    async def build(self, *, document: Document) -> str | None:
        return self._content
