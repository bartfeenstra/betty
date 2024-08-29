"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, final

import aiofiles
from typing_extensions import override

from betty.ancestry import Person
from betty.asyncio import gather
from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from betty.generate import GenerateSiteEvent
from betty.locale.localizable import _, Localizable
from betty.project.extension import Extension

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin import PluginIdentifier
    from betty.machine_name import MachineName
    from collections.abc import Sequence


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
    localizer = await event.project.localizers.get(locale)
    private_label = localizer._("private")
    people = {
        person.id: {
            "id": person.id,
            "label": person.label.localize(localizer)
            if person.public
            else private_label,
            "url": event.project.url_generator.generate(person, "text/html"),
            "parentIds": [parent.id for parent in person.parents],
            "childIds": [child.id for child in person.children],
            "private": person.private,
        }
        for person in event.project.ancestry[Person]
    }
    people_json = json.dumps(people)
    async with aiofiles.open(
        event.project.configuration.localize_www_directory_path(locale) / "people.json",
        mode="w",
    ) as f:
        await f.write(people_json)


@final
class Trees(Extension, WebpackEntryPointProvider):
    """
    Provide interactive family trees for use in web pages.
    """

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return "trees"

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {Webpack}

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

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Trees")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _(
            'Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.'
        )
