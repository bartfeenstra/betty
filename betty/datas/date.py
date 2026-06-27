"""
Date data.
"""

from __future__ import annotations

from typing import final

from betty.data import DataDefinition
from betty.date import Date, DateExpression, DateRange
from betty.localizables.gettext import _
from betty.porters.date import DateExpressionPorter


@final
class DateExpressionDefinition(DataDefinition[DateExpression]):
    """
    The data definition for a date expression.
    """

    def __init__(self):
        super().__init__(
            label=_("Date"),
            porter=DateExpressionPorter(),
            samples=[Date, DateRange],
        )
