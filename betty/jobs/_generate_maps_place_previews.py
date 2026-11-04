"""
Maps place previews jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.entities.place import Place
from betty.file import write
from betty.job import Job
from betty.jobs.generate_entity import GenerateEntity
from betty.media_types import html

if TYPE_CHECKING:
    from babel import Locale

    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class _GenerateMapsPlacePreviews(Job):
    def __init__(self, *, project: Project):
        super().__init__("maps:generate-place-previews", priority=True)
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await scheduler.add(
            *(
                _GenerateMapsPlacePreview(place, locale.locale, project=self._project)
                for locale in self._project.locales
                for place in self._project.ancestry[Place]
                if place.coordinates
            )
        )


@final
class _GenerateMapsPlacePreview(Job):
    def __init__(self, place: Place, locale: Locale, /, *, project: Project):
        super().__init__(
            f"maps:generate-place-preview:{place.id}:{locale}",
            dependencies=[GenerateEntity.id_for(place)],
        )
        self._place = place
        self._locale = locale
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        context = scheduler.context
        jinja = await self._project.jinja
        place_path = (
            self._project.localize_www_directory(self._locale)
            / self._place.definition.id
            / self._place.id
        )
        rendered_html = await jinja.get_template(
            "component/maps/selected-place-preview.html.j2",
        ).render_async(
            document=await self._project.new_document(
                html,
                context=context,
                localizer=await self._project.localizers.get(self._locale),
            ),
            place=self._place,
        )
        await write(place_path / "-maps-place-preview.html", rendered_html)
