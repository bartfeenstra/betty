"""
The ``to_language_tag`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.locale import to_language_tag

if TYPE_CHECKING:
    from babel import Locale


@final
@JinjaFilterDefinition("to-language-tag", auto=True)
class ToLanguageTag(JinjaFilter):
    """
    .. plugin:: jinja-filter:to-language-tag.
    """

    def __call__(  # noqa: D102
        self, locale: Locale | None, /
    ) -> str:
        return to_language_tag(locale)
