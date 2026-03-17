"""
The ``negotiate_has_dates`` Jinja filter.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, final

from jinja2 import pass_context

from betty.jinja import JinjaFilterDefinition
from betty.jinja.filter import JinjaFilter
from betty.plugins.jinja_filter.select_has_dates import SelectHasDates

if TYPE_CHECKING:
    from collections.abc import Iterable

    from jinja2.runtime import Context

    from betty.ancestry.date import HasDate
    from betty.date import ResolvableDate


@final
@JinjaFilterDefinition("negotiate-has-dates", auto=True)
class NegotiateHasDates(JinjaFilter):
    """
    Try to find an object whose date falls in the given date.

    .. plugin:: jinja-filter:negotiate-has-dates
    """

    _select_has_dates = SelectHasDates()

    @pass_context
    def __call__(
        self,
        context: Context,
        has_dates: Iterable[HasDate],
        /,
        date: ResolvableDate | None,
    ) -> HasDate | None:
        """
        :param date: A date to select by. If ``None``, then today's date is used.
        """
        with suppress(StopIteration):
            return next(self._select_has_dates(context, has_dates, date))
        return None
