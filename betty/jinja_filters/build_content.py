"""
The ``build_content`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from jinja2 import pass_context
from markupsafe import Markup

from betty.content import Content, build
from betty.factory import Factory, Manufacturable
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from jinja2.runtime import Context

    from betty.service_level import ServiceLevel


@final
@JinjaFilterDefinition("build-content", auto=True)
class BuildContent(JinjaFilter, Manufacturable):
    """
    Build content from content configuration.

    .. plugin:: jinja-filter:build-content
    """

    def __init__(self, *, factory: Factory):
        self._factory = factory

    @override
    @classmethod
    async def new(cls, services: ServiceLevel, /) -> Self:
        return cls(factory=services.factory)

    @pass_context
    async def __call__(  # noqa: D102
        self,
        context: Context,
        contents: Iterable[Content],
        /,
    ) -> Markup:
        return await build(context_document(context), contents) or Markup("")
