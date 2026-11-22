"""
The ``url`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final, override

from jinja2 import pass_context

from betty.collections.mapping.dict import empty_frozen_dict
from betty.factory import Manufacturable
from betty.jinja import context_document
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.media_types import html
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from jinja2.runtime import Context

    from betty.locale import ResolvableLocale
    from betty.media_type import MediaTypeMatcher
    from betty.url_generator import UrlGenerator


@final
@JinjaFilterDefinition("url", auto=True)
class Url(JinjaFilter, Manufacturable):
    """
    Generate a URL for a resource.

    .. plugin:: jinja-filter:url
    """

    def __init__(self, *, media_types: MediaTypeMatcher, url_generator: UrlGenerator):
        self._media_types = media_types
        self._url_generator = url_generator

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(
            media_types=project.app.known_media_types,
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
            media_type=html,
            locale=locale or context_document(context).localizer.locale,
            query=query,
        )
