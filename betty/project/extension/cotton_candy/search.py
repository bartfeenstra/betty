"""
Provide Cotton Candy's search functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.file import File
from betty.ancestry.person import Person
from betty.ancestry.place import Place

if TYPE_CHECKING:
    from betty.model import Entity
    from betty.project import Project
    from betty.locale.localizer import Localizer
    from betty.job import Context
    from collections.abc import AsyncIterable, Mapping


class Index:
    """
    Build search indexes.
    """

    def __init__(
        self,
        project: Project,
        job_context: Context | None,
        localizer: Localizer,
    ):
        self._project = project
        self._job_context = job_context
        self._localizer = localizer

    async def build(self) -> AsyncIterable[Mapping[str, str]]:
        """
        Build the search index.
        """
        async for entry in self._build_people():
            yield entry
        async for entry in self._build_places():
            yield entry
        async for entry in self._build_files():
            yield entry

    async def _build_people(self) -> AsyncIterable[Mapping[str, str]]:
        for person in self._project.ancestry[Person]:
            entry = await self._build_person(person)
            if entry is not None:
                yield entry

    async def _build_places(self) -> AsyncIterable[Mapping[str, str]]:
        for place in self._project.ancestry[Place]:
            entry = await self._build_place(place)
            if entry is not None:
                yield entry

    async def _build_files(self) -> AsyncIterable[Mapping[str, str]]:
        for file in self._project.ancestry[File]:
            entry = await self._build_file(file)
            if entry is not None:
                yield entry

    async def _render_entity(self, entity: Entity) -> str:
        return await self._project.jinja2_environment.select_template(
            [
                f"search/result--{entity.plugin_id()}.html.j2",
                "search/result.html.j2",
            ]
        ).render_async(
            {
                "job_context": self._job_context,
                "localizer": self._localizer,
                "entity": entity,
            }
        )

    async def _build_person(self, person: Person) -> Mapping[str, str] | None:
        if person.private:
            return None

        names = []
        for name in person.names:
            if name.individual is not None:
                names.append(name.individual.lower())
            if name.affiliation is not None:
                names.append(name.affiliation.lower())
        if not names:
            return None
        return {
            "text": " ".join(names),
            "result": await self._render_entity(person),
        }

    async def _build_place(self, place: Place) -> Mapping[str, str] | None:
        if place.private:
            return None

        return {
            "text": " ".join(
                translation.lower()
                for name in place.names
                for translation in name.translations.values()
            ),
            "result": await self._render_entity(place),
        }

    async def _build_file(self, file: File) -> Mapping[str, str] | None:
        if file.private:
            return None

        if not file.description:
            return None
        return {
            "text": " ".join(
                description.lower()
                for description in file.description.translations.values()
            ),
            "result": await self._render_entity(file),
        }
