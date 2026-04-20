"""
Render HTML.
"""

from typing import Self, override

from betty.factory import Manufacturable
from betty.html.url import generate_urls
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import AllEnumeration
from betty.media_type import MediaType
from betty.media_type.media_types import HTML
from betty.project import Project
from betty.render import Renderer, RendererDefinition
from betty.url import UrlGenerator

_ATTRIBUTES = ("href", "src")


@RendererDefinition(
    "html",
    label="HTML",
    description=_(
        "The values of the following HTML attributes will automatically be replaced with the URLs generated from them where possible: {attributes}"
    ).format(attributes=AllEnumeration(*_ATTRIBUTES)),
)
class Html(Manufacturable, Renderer):
    """
    .. plugin:: renderer:html.
    """

    def __init__(self, *, url_generator: UrlGenerator):
        self._url_generator = url_generator

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(url_generator=await project.url_generator)

    @override
    @property
    def media_type(self) -> MediaType:
        return HTML

    @override
    async def render(self, content: str, /) -> str:
        return generate_urls(content, _ATTRIBUTES, url_generator=self._url_generator)
