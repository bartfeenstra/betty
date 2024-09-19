"""
Data types to represent names.
"""

from __future__ import annotations

from typing import final, TYPE_CHECKING

from betty.ancestry.date import HasDate
from betty.locale.localizable import (
    StaticTranslationsLocalizable,
    ShorthandStaticTranslations,
)

if TYPE_CHECKING:
    from betty.date import Datey


@final
class Name(StaticTranslationsLocalizable, HasDate):
    """
    A name.

    A name can be translated, and have a date expressing the period the name was in use.
    """

    def __init__(
        self,
        translations: ShorthandStaticTranslations,
        *,
        date: Datey | None = None,
    ):
        super().__init__(
            translations,
            date=date,
        )
