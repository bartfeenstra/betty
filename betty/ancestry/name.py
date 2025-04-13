"""
Data types to represent names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.ancestry.date import HasDate
from betty.locale.localizable import (
    RequiredStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
)

if TYPE_CHECKING:
    from betty.date import Datey


@final
class Name(HasDate):
    """
    A name.

    A name can be translated, and have a date expressing the period the name was in use.
    """

    #: The name.
    name = RequiredStaticTranslationsLocalizableAttr("name")

    def __init__(
        self,
        name: ShorthandStaticTranslations,
        *,
        date: Datey | None = None,
    ):
        super().__init__(date=date)
        self.name = name
