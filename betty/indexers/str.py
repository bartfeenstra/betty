"""
String search indexers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.localized import LocalizedStr
from betty.search import FieldIndexer

if TYPE_CHECKING:
    from betty.localizer import Localizer
    from betty.project import Project


@final
class StrIndexer(FieldIndexer[str]):
    """
    Index strings.
    """

    @override
    async def index(
        self, data: str, /, *, localizer: Localizer, project: Project
    ) -> LocalizedStr | None:
        if data:
            return LocalizedStr(data, locale=None)
        return None
