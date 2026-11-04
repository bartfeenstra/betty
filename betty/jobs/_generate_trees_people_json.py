from __future__ import annotations

import json
from asyncio import gather
from typing import TYPE_CHECKING, final, override

from betty.entities.person import Person
from betty.file import write
from betty.job import Job
from betty.jobs.generate_www_directory import GenerateWwwDirectory
from betty.media_types import html

if TYPE_CHECKING:
    from babel import Locale

    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class _GenerateTreesPeopleJson(Job):
    def __init__(self, *, project: Project):
        super().__init__(
            "trees:generate-people-json", dependencies=[GenerateWwwDirectory.id_for]
        )
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await gather(
            *(
                self._generate_people_json_for_locale(locale.locale)
                for locale in self._project.locales
            )
        )

    async def _generate_people_json_for_locale(self, locale: Locale, /) -> None:
        url_generator = await self._project.url_generator
        localizer = await self._project.localizers.get(locale)
        private_label = localizer.translate._("private")
        people = {
            person.id: {
                "id": person.id,
                "label": localizer.localize(person.label)
                if person.public
                else private_label,
                "url": url_generator.generate(person, media_type=html),
                "parentIds": [parent.id for parent in person.parents],
                "childIds": [child.id for child in person.children],
                "private": person.private,
            }
            for person in self._project.ancestry[Person]
        }
        await write(
            self._project.localize_www_directory(locale) / "people.json",
            json.dumps(people),
        )
