"""
Jobs for the Trees extension.
"""

from __future__ import annotations

import json
from asyncio import gather
from typing import TYPE_CHECKING

import aiofiles
from aiofiles.os import makedirs
from typing_extensions import override

from betty.ancestry.person import Person
from betty.job import Job
from betty.media_type.media_types import HTML
from betty.project import ProjectContext

if TYPE_CHECKING:
    from babel import Locale

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
        self, scheduler: Scheduler[ProjectContext], locale: Locale
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
        await makedirs(project.localize_www_directory_path(locale), exist_ok=True)
        async with aiofiles.open(
            project.localize_www_directory_path(locale) / "people.json",
            mode="w",
        ) as f:
            await f.write(people_json)
