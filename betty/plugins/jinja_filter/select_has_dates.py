"""
The ``select_has_dates`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from jinja2 import pass_context

from betty.jinja import JinjaFilterDefinition
from betty.jinja.filter import JinjaFilter

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from jinja2.runtime import Context

    from betty.date import ResolvableDate
    from betty.entity.has_date import HasDate


@final
@JinjaFilterDefinition("select-has-dates", auto=True)
class SelectHasDates(JinjaFilter):
    """
    Select all objects whose date falls in the given date.

    .. plugin:: jinja-filter:select-has-dates
    """

    @pass_context
    def __call__(
        self,
        context: Context,
        has_dates: Iterable[HasDate],
        /,
        date: ResolvableDate | None,
    ) -> Iterator[HasDate]:
        """
        :param date: A date to select by. If ``None``, then today's date is used.
        """
        if date is None:
            date = context.resolve_or_missing("today")
        return filter(
            lambda dated: (
                dated.date is None or dated.date.comparable and dated.date in date
            ),
            has_dates,
        )
