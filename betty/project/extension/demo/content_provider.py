"""
Dynamic content.
"""

from typing import Any, Self

from typing_extensions import override

from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.job import Context
from betty.locale.localizable import Plain
from betty.plugin import ClassedPlugin
from betty.project import Project
from betty.project.factory import ProjectDependentFactory


@ContentProviderDefinition(
    id="demo-front-page-content",
    label=Plain("Front page content (demo)"),
)
class _FrontPageContent(ContentProvider, ClassedPlugin, ProjectDependentFactory):
    def __init__(self, project: Project):
        self._project = project

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project)

    @override
    async def provide(
        self, *, locale: str, page_resource: Any, job_context: Context | None = None
    ) -> str:
        localizers = await self._project.localizers
        jinja2_environment = await self._project.jinja2_environment
        return await jinja2_environment.get_template(
            "demo-front-page-content.html.j2"
        ).render_async(
            job_context=job_context,
            localizer=localizers.get(locale),
        )


@ContentProviderDefinition(
    id="demo-front-page-summary",
    label=Plain("Front page summary (demo)"),
)
class _FrontPageSummary(ContentProvider, ClassedPlugin, ProjectDependentFactory):
    def __init__(self, project: Project):
        self._project = project

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project)

    @override
    async def provide(
        self, *, locale: str, page_resource: Any, job_context: Context | None = None
    ) -> str:
        localizers = await self._project.localizers
        jinja2_environment = await self._project.jinja2_environment
        return await jinja2_environment.get_template(
            "demo-front-page-summary.html.j2"
        ).render_async(
            job_context=job_context,
            localizer=localizers.get(locale),
        )
