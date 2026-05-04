"""
The ``html_lang`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from jinja2 import pass_context
from markupsafe import Markup

from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.locale import LocalizedStr, to_language_tag

if TYPE_CHECKING:
    from jinja2.runtime import Context


_CHARACTER_ORDER_TO_HTML_LANG_MAP = {
    "left-to-right": "ltr",
    "right-to-left": "rtl",
}


@final
@JinjaFilterDefinition("html-lang", auto=True)
class HtmlLang(JinjaFilter):
    """
    Optionally add the necessary HTML to indicate the localized string has a different locale than the surrounding HTML.

    .. plugin:: jinja-filter:html-lang
    """

    @pass_context
    def __call__(  # noqa: D102
        self, context: Context, has_locale: str, /
    ) -> str | Markup:
        if not isinstance(has_locale, LocalizedStr):
            return has_locale

        localizer = context_document(context).localizer
        result: str | Markup = has_locale
        if has_locale.locale != localizer.locale:
            localizer_dir = _CHARACTER_ORDER_TO_HTML_LANG_MAP[
                localizer.locale.character_order
            ]
            if has_locale.locale is None:
                has_locale_dir = "auto"
            else:
                has_locale_dir = _CHARACTER_ORDER_TO_HTML_LANG_MAP[
                    has_locale.locale.character_order
                ]
            dir_attribute = (
                f' dir="{has_locale_dir}"' if has_locale_dir != localizer_dir else ""
            )
            result = f'<span lang="{to_language_tag(has_locale.locale)}"{dir_attribute}>{has_locale}</span>'
        if context.eval_ctx.autoescape:
            result = Markup(result)
        return result
