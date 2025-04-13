"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from asyncio import Semaphore, gather
from pathlib import Path
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.place import Place
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.generate import GenerateSiteEvent
from betty.project.generate.file import create_file

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin import PluginIdentifier
    from betty.project.extension import Extension


async def _generate_place_previews(event: GenerateSiteEvent) -> None:
    semaphore = Semaphore(64)
    await gather(
        *(
            _generate_place_preview_for_locale(semaphore, event, locale, place)
            for locale in event.project.configuration.locales
            for place in event.project.ancestry[Place]
            if place.coordinates
        )
    )


async def _generate_place_preview_for_locale(
    semaphore: Semaphore, event: GenerateSiteEvent, locale: str, place: Place
) -> None:
    async with semaphore:
        job_context = event.job_context
        project = job_context.project
        app = project.app
        jinja2_environment = await project.jinja2_environment
        place_path = (
            project.configuration.localize_www_directory_path(locale)
            / place.plugin_id()
            / place.id
        )
        rendered_html = await jinja2_environment.get_template(
            "maps/selected-place-preview.html.j2",
        ).render_async(
            job_context=job_context,
            localizer=await app.localizers.get(locale),
            place=place,
        )
        async with create_file(place_path / "-maps-place-preview.html") as f:
            await f.write(rendered_html)


@final
class Maps(ShorthandPluginBase, EntryPointProvider):
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
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, _generate_place_previews)
