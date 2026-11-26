"""
The ``url`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final, override

from jinja2 import pass_context

from betty.collections.mapping.dict import empty_frozen_dict
from betty.content_types import html
from betty.factory import Manufacturable
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from jinja2.runtime import Context

    from betty.content_type import MediaTypeNegotiator
    from betty.locale import ResolvableLocale
    from betty.url_generator import UrlGenerator


@final
@JinjaFilterDefinition("url", auto=True)
class Url(JinjaFilter, Manufacturable):
    """
    Generate a URL for a resource.

    .. plugin:: jinja-filter:url
    """

    def __init__(
        self, *, content_types: MediaTypeNegotiator, url_generator: UrlGenerator
    ):
        self._content_types = content_types
        self._url_generator = url_generator

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(
            content_types=project.app.known_content_types,
            url_generator=await project.url_generator,
        )

    @pass_context
    async def __call__(  # noqa: D102
        self,
        context: Context,
        resource: Any,
        /,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        query: Mapping[str, Sequence[str]] = empty_frozen_dict,
    ) -> str:
        return self._url_generator.generate(
            resource,
            absolute=absolute,
            fragment=fragment,
            content_type=html,
            locale=locale or context_document(context).localizer.locale,
            query=query,
        )
