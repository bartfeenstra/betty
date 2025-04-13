"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

import json
from asyncio import gather
from pathlib import Path
from typing import TYPE_CHECKING, final

import aiofiles
from typing_extensions import override

from betty.ancestry.person import Person
from betty.locale.localizable import _
from betty.media_type.media_types import HTML
from betty.plugin import ShorthandPluginBase
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.generate import GenerateSiteEvent

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin import PluginIdentifier
    from betty.project.extension import Extension


async def _generate_people_json(event: GenerateSiteEvent) -> None:
    await gather(
        *(
            _generate_people_json_for_locale(event, locale)
            for locale in event.project.configuration.locales
        )
    )


async def _generate_people_json_for_locale(
    event: GenerateSiteEvent, locale: str
) -> None:
    project = event.project
    url_generator = await project.url_generator
    localizers = await project.localizers
    localizer = await localizers.get(locale)
    private_label = localizer._("private")
    people = {
        person.id: {
            "id": person.id,
            "label": person.label.localize(localizer)
            if person.public
            else private_label,
            "url": url_generator.generate(person, media_type=HTML),
            "parentIds": [parent.id for parent in person.parents],
            "childIds": [child.id for child in person.children],
            "private": person.private,
        }
        for person in project.ancestry[Person]
    }
    people_json = json.dumps(people)
    async with aiofiles.open(
        project.configuration.localize_www_directory_path(locale) / "people.json",
        mode="w",
    ) as f:
        await f.write(people_json)


@final
class Trees(ShorthandPluginBase, EntryPointProvider):
    """
    Provide interactive family trees for use in web pages.
    """

    _plugin_id = "trees"
    _plugin_label = _("Trees")
    _plugin_description = _(
        'Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.'
    )

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {Webpack}

    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / "assets"

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, _generate_people_json)

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
