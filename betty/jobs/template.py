"""
Jobs to generate HTML pages for entities.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from asyncio import gather
from typing import TYPE_CHECKING, final, override

from betty.file import write
from betty.jinja import TemplateNames, resolve_template_names
from betty.job import Job
from betty.media_type import MediaType, match_extension
from betty.typing import empty_frozen_dict

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    import jinja2
    from jinja2 import Template

    from betty.jinja import ResolvableTemplateNames, TemplateData
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class Template(Job):
    """
    Render a template to a file.
    """

    __slots__ = ("_data", "_destination", "_template")

    def __init__(
        self,
        job_id: str,
        template: jinja2.Template,
        destination: Path,
        data: TemplateData = empty_frozen_dict,
        /,
        *,
        dependencies: Iterable[str] = (),
        dependents: Iterable[str] = (),
        priority: bool = False,
    ):
        super().__init__(
            job_id, dependencies=dependencies, dependents=dependents, priority=priority
        )
        self._template = template
        self._destination = destination
        self._data = data

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await write(self._destination, await self._template.render_async(**self._data))


class _ResourceTemplate[ResourceT](Job, metaclass=ABCMeta):
    __slots__ = ("_project", "_resource", "_www_destination")

    def __init__(
        self,
        resource: ResourceT,
        www_destination: Path,
        /,
        *,
        project: Project,
        dependencies: Iterable[str] = (),
        dependents: Iterable[str] = (),
        priority: bool = False,
    ):
        super().__init__(
            self.id_for(resource, project=project),
            dependencies=dependencies,
            dependents=dependents,
            priority=priority,
        )
        self._www_destination = www_destination
        self._project = project
        self._resource = resource

    @classmethod
    @abstractmethod
    def template(cls, resource: ResourceT, /) -> ResolvableTemplateNames:
        """
        Get the template name(s).
        """

    @classmethod
    @abstractmethod
    def id_prefix(cls, resource: ResourceT, /) -> ResolvableTemplateNames:
        """
        Get the job ID prefix.
        """

    @final
    @classmethod
    def id_for(cls, resource: ResourceT, /, *, project: Project) -> str:
        """
        Get the job ID.
        """
        return f"{cls.id_prefix(resource)}:{cls._match_extension(resolve_template_names(cls.template(resource)), project=project)[1]}"

    @final
    @classmethod
    def _match_extension(
        cls, templates: TemplateNames, /, *, project: Project
    ) -> tuple[MediaType, str]:
        return match_extension(templates[0][:-3], project.upstream.media_types)


class ResourceTemplate[ResourceT](_ResourceTemplate[ResourceT], metaclass=ABCMeta):
    """
    Render a template to files for a resource.
    """

    @final
    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        jinja = await self._project.jinja
        templates = resolve_template_names(self.template(self._resource))
        template = jinja.select_template(templates)
        media_type, extension = self._match_extension(templates, project=self._project)
        await gather(*[
            scheduler.add(
                Template(
                    f"{self.id}:{locale.locale}.",
                    template,
                    self._project.localize_www_directory(locale.locale)
                    / self._www_destination
                    / f"index{extension}",
                    {
                        "document": await self._project.new_document(
                            self._resource,
                            self._resource,
                            context=scheduler.context,
                            localizer=await self._project.localizers.get(locale.locale),
                            media_type=media_type,
                        )
                    },
                ),
            )
            for locale in self._project.locales
        ])


class ResourceListTemplate[ResourceT](_ResourceTemplate[ResourceT], metaclass=ABCMeta):
    """
    Render a template to files for a list of resources.
    """

    @final
    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        # @todo Paginate resources. Copy the relevant code from GenerateEntityTypesHtml
        raise NotImplementedError
