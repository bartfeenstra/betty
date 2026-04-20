"""
The ``url`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final, override

from jinja2 import pass_context

from betty.factory import Manufacturable
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.media_type import MediaType
from betty.media_type.media_types import HTML
from betty.project import Project

if TYPE_CHECKING:
    from jinja2.runtime import Context

    from betty.locale import ResolvableLocale
    from betty.url import UrlGenerator


@final
@JinjaFilterDefinition("url", auto=True)
class Url(JinjaFilter, Manufacturable):
    """
    Generate a URL for a resource.

    .. plugin:: jinja-filter:url
    """

    def __init__(self, url_generator: UrlGenerator, /):
        self._url_generator = url_generator

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(await project.url_generator)

    @pass_context
    async def __call__(  # noqa: D102
        self,
        context: Context,
        resource: Any,
        locale: ResolvableLocale | None = None,
        media_type: str | None = None,
        **kwargs: Any,
    ) -> str:
        return self._url_generator.generate(
            resource,
            media_type=MediaType(media_type) if media_type else HTML,
            locale=locale or context_document(context).localizer.locale,
            **kwargs,
        )
