"""
The ``format_datetime_datetime`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from babel.dates import format_date
from jinja2 import pass_context

from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition

if TYPE_CHECKING:
    import datetime

    from jinja2.runtime import Context


@final
@JinjaFilterDefinition("format-datetime-datetime", auto=True)
class FormatDatetimeDatetime(JinjaFilter):
    """
    Format a datetime date to a human-readable string.

    .. plugin:: jinja-filter:format-datetime-datetime
    """

    @pass_context
    def __call__(  # noqa: D102
        self, context: Context, datetime_datetime: datetime.datetime, /
    ) -> str:
        localizer = context_document(context).localizer
        return format_date(datetime_datetime, "long", locale=localizer.locale)
