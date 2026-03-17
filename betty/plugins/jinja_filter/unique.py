"""
The ``unique`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from jinja2.async_utils import auto_aiter

from betty.jinja import JinjaFilterDefinition
from betty.jinja.filter import JinjaFilter

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable


@final
@JinjaFilterDefinition("unique", auto=True)
class Unique(JinjaFilter):
    """
    Iterate over an iterable of values and only yield those values that have not been yielded before.

    .. plugin:: jinja-filter:unique
    """

    async def __call__[T](  # noqa: D102
        self, values: Iterable[T], /
    ) -> AsyncIterator[T]:
        seen = []
        async for value in auto_aiter(values):
            if value not in seen:
                yield value
                seen.append(value)
