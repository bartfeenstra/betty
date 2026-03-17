"""
The ``localize`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from jinja2 import pass_context

from betty.jinja import context_localizer
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition

if TYPE_CHECKING:
    from jinja2.runtime import Context

    from betty.locale.localizable import Localizable


@final
@JinjaFilterDefinition("localize", auto=True)
class Localize(JinjaFilter):
    """
    Localize a value using the context's current localizer.

    .. plugin:: jinja-filter:localize
    """

    @pass_context
    def __call__(  # noqa: D102
        self, context: Context, localizable: Localizable, /
    ) -> str:
        return localizable.localize(context_localizer(context))
