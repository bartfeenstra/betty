"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

import json
from asyncio import gather
from pathlib import Path
from typing import TYPE_CHECKING, final

import aiofiles
from aiofiles.os import makedirs
from typing_extensions import override

from betty.ancestry.person import Person
from betty.job import Job
from betty.locale.localizable import Plain, _
from betty.media_type.media_types import HTML
from betty.project import ProjectContext
from betty.project.extension import ExtensionDefinition
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.generate import Generator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler


class _GeneratePeopleJson(Job[ProjectContext]):
    def __init__(self):
        super().__init__("trees:generate-people-json")

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        await gather(
            *(
                self._generate_people_json_for_locale(scheduler, locale)
                for locale in scheduler.context.project.configuration.locales
            )
        )

    async def _generate_people_json_for_locale(
        self, scheduler: Scheduler[ProjectContext], locale: str
    ) -> None:
        project = scheduler.context.project
        url_generator = await project.url_generator
        localizers = await project.localizers
        localizer = localizers.get(locale)
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
        await makedirs(
            project.configuration.localize_www_directory_path(locale), exist_ok=True
        )
        async with aiofiles.open(
            project.configuration.localize_www_directory_path(locale) / "people.json",
            mode="w",
        ) as f:
            await f.write(people_json)


@final
@ExtensionDefinition(
    id="trees",
    label=Plain("Trees"),
    description=_(
        'Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.'
    ),
    depends_on={Webpack.plugin},
    assets_directory_path=Path(__file__).parent / "assets",
)
class Trees(Generator, EntryPointProvider):
    """
    Provide interactive family trees for use in web pages.
    """

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(_GeneratePeopleJson())

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
