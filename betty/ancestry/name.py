"""
Data types to represent names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.ancestry.date import HasDate
from betty.locale.localizable.gettext import _
from betty.locale.localizable.property import LocalizableProperty

if TYPE_CHECKING:
    from betty.date import DateLike
    from betty.locale.localizable import LocalizableLike


@final
class Name(HasDate):
    """
    A name.

    A name can be translated, and have a date expressing the period the name was in use.
    """

    name = LocalizableProperty(label=_("Name"))

    def __init__(
        self,
        name: LocalizableLike,
        *,
        date: DateLike | None = None,
    ):
        super().__init__(date=date)
        self.name = name
