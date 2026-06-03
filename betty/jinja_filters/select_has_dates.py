"""
The ``select_has_dates`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from jinja2 import pass_context

from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from jinja2.runtime import Context

    from betty.attrs.date import HasAnyDate
    from betty.date import AnyDate


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
        has_dates: Iterable[HasAnyDate],
        /,
        date: AnyDate | None,
    ) -> Iterator[HasAnyDate]:
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
