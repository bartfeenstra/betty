"""
The ``file-url`` Jinja filter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from jinja2 import pass_context

from betty.factory import Manufacturable
from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition
from betty.jobs.generate_files import url
from betty.project import Project

if TYPE_CHECKING:
    from jinja2.runtime import Context

    from betty.entities.file import File
    from betty.url_generator import UrlGenerator


@final
@JinjaFilterDefinition("file-url", auto=True)
class FileUrl(JinjaFilter, Manufacturable):
    """
    Generate a URL to a :py:class:`betty.entities.file.File`'s file.

    .. plugin:: jinja-filter:file-url
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
        self, context: Context, file: File, /, *, absolute: bool = False
    ) -> str:
        return self._url_generator.generate(url(file), absolute=absolute)
