"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.place import Place
from betty.job import Job
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project import ProjectContext
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.generate import Generator
from betty.project.generate.file import create_file

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.plugin import PluginIdentifier
    from betty.project.extension import Extension


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
    def __init__(self, place_id: str, locale: str):
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
            project.configuration.localize_www_directory_path(self._locale)
            / place.plugin_id()
            / place.id
        )
        rendered_html = await jinja2_environment.get_template(
            "maps/selected-place-preview.html.j2",
        ).render_async(
            job_context=context, localizer=localizers.get(self._locale), place=place
        )
        async with create_file(place_path / "-maps-place-preview.html") as f:
            await f.write(rendered_html)


@final
class Maps(ShorthandPluginBase, Generator, EntryPointProvider):
    """
    Provide interactive maps for use on web pages.
    """

    _plugin_id = "maps"
    _plugin_label = _("Maps")
    _plugin_description = _("Display interactive maps")

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {Webpack}

    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / "assets"

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(_GeneratePlacePreviews())
