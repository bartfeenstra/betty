"""
String search indexers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.localized import LocalizedStr
from betty.search import FieldIndexer

if TYPE_CHECKING:
    from betty.localizer import Localizer


@final
class StrIndexer(FieldIndexer[str]):
    """
    Index strings.
    """

    @override
    async def index(self, data: str, /, *, localizer: Localizer) -> LocalizedStr:
        return LocalizedStr(data, locale=None)
