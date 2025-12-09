"""
Jobs for the Maps extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.place import Place
from betty.job import Job
from betty.project import ProjectContext
from betty.project.generate.file import create_file

if TYPE_CHECKING:
    from babel import Locale

    from betty.job.scheduler import Scheduler


class _GeneratePlacePreviews(Job[ProjectContext]):
    def __init__(self):
        super().__init__("maps:generate-place-previews", priority=True)

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        await scheduler.add(
            *(
                _GeneratePlacePreview(place.id, locale)
                for locale in project.configuration.locales
                for place in project.ancestry[Place]
                if place.coordinates
            )
        )


class _GeneratePlacePreview(Job[ProjectContext]):
    def __init__(self, place_id: str, locale: Locale):
        super().__init__(f"maps:generate-place-preview:{place_id}:{locale}")
        self._place_id = place_id
        self._locale = locale

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        context = scheduler.context
        project = context.project
        place = project.ancestry[Place][self._place_id]
        app = project.app
        localizers = await app.localizers
        jinja2_environment = await project.jinja2_environment
        place_path = (
            project.localize_www_directory_path(self._locale)
            / place.plugin().id
            / place.public_id
        )
        rendered_html = await jinja2_environment.get_template(
            "maps/selected-place-preview.html.j2",
        ).render_async(
            resource=await project.new_resource_context(
                job_context=context,
                localizer=localizers.get(self._locale),
            ),
            place=place,
        )
        async with create_file(place_path / "-maps-place-preview.html") as f:
            await f.write(rendered_html)
