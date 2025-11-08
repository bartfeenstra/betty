"""
Dynamic content.
"""

from typing import Any, Self

from typing_extensions import override

from betty.config import DefaultConfigurable
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.html import newlines_to_paragraphs
from betty.job import Context
from betty.locale.localizable import _
from betty.locale.localizable.config import StaticTranslationsConfiguration
from betty.plugin import ClassedPlugin
from betty.project import Project
from betty.project.factory import ProjectDependentFactory


@ContentProviderDefinition(
    id="plain-text",
    label=_("Plain text"),
)
class PlainText(
    ContentProvider,
    ClassedPlugin,
    DefaultConfigurable[StaticTranslationsConfiguration],
    ProjectDependentFactory,
):
    """
    Plain text content.
    """

    def __init__(
        self, project: Project, configuration: StaticTranslationsConfiguration
    ):
        super().__init__(configuration=configuration)
        self._project = project

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project, configuration=cls.new_default_configuration())

    @override
    @classmethod
    def new_default_configuration(cls) -> StaticTranslationsConfiguration:
        return StaticTranslationsConfiguration()

    @override
    async def provide(
        self, *, locale: str, page_resource: Any, job_context: Context | None = None
    ) -> str:
        localizers = await self._project.localizers
        return newlines_to_paragraphs(
            self.configuration.localize(localizers.get(locale))
        )
