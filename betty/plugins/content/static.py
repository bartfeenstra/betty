"""
Static content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import Content, ContentDefinition
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from betty.document import Document
    from betty.service_level import ServiceLevel


@final
@ContentDefinition("static", label=_("Static content"))
class Static(Content, Manufacturable):
    """
    .. plugin:: content:static.
    """

    def __init__(self, content: str | None = None, /):
        self._content = content

    @override
    @classmethod
    async def new(cls, services: ServiceLevel, /) -> Self:
        return cls()

    @override
    async def build(self, *, document: Document) -> str | None:
        return self._content
