"""
The ``build_content`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from jinja2 import pass_context
from markupsafe import Markup

from betty.content_builder import ContentBuilder, build
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from jinja2.runtime import Context


@final
@JinjaFilterDefinition("build-content", auto=True)
class BuildContent(JinjaFilter):
    """
    Build content from content configuration.

    .. plugin:: jinja-filter:build-content
    """

    @pass_context
    async def __call__(  # noqa: D102
        self,
        context: Context,
        contents: Iterable[ContentBuilder],
        /,
    ) -> Markup:
        return await build(context_document(context), contents) or Markup("")
