"""
Dynamic content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from typing_extensions import override

from betty.config import DefaultConfigurable
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.factory import IndependentFactory
from betty.html import newlines_to_paragraphs
from betty.locale.localizable import _
from betty.locale.localizable.config import StaticTranslationsConfiguration
from betty.plugin import ClassedPlugin
from betty.project.factory import ProjectDependentFactory

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.project import Project
    from betty.resource import Context


@ContentProviderDefinition(
    id="plain-text",
    label=_("Plain text"),
)
class PlainText(
    ContentProvider,
    ClassedPlugin,
    DefaultConfigurable[StaticTranslationsConfiguration],
    IndependentFactory,
):
    """
    Plain text content.
    """

    @override
    @classmethod
    async def new(cls) -> Self:
        return cls(configuration=cls.new_default_configuration())

    @override
    @classmethod
    def new_default_configuration(cls) -> StaticTranslationsConfiguration:
        return StaticTranslationsConfiguration()

    @override
    async def provide(self, *, resource: Context) -> str | None:
        return newlines_to_paragraphs(
            self.configuration.localize(resource["localizer"])
        )


class Template(ContentProvider, ClassedPlugin, ProjectDependentFactory):
    """
    Provides content by rendering a Jinja2 template.
    """

    def __init__(self, project: Project, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._project = project

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project)

    @override
    async def provide(self, *, resource: Context) -> str | None:
        jinja2_environment = await self._project.jinja2_environment
        rendered_content = (
            await jinja2_environment.get_template(
                f"content/{self.plugin.id}.html.j2"
            ).render_async(
                resource=resource,
                **await self._provide_data(resource),
            )
        ).strip()
        if rendered_content:
            return rendered_content
        return None

    async def _provide_data(self, resource: Context) -> Mapping[str, Any]:
        return {}


@ContentProviderDefinition(
    id="notes",
    label=_("Notes"),
)
class Notes(Template):
    """
    Render a page resource's notes, if it has any.
    """
