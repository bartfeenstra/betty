"""
Provide Cotton Candy's search functionality.
"""
from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Any

from betty.app import App
from betty.locale import Localizer
from betty.model import get_entity_type_name, Entity
from betty.model.ancestry import Person, Place, File
from betty.string import camel_case_to_snake_case
from betty.task import Context


class Index:
    def __init__(
        self,
        app: App,
        task_context: Context | None,
        localizer: Localizer,
    ):
        self._app = app
        self._task_context = task_context
        self._localizer = localizer

    async def build(self) -> AsyncIterable[dict[str, str]]:
        async for entry in self._build_people():
            yield entry
        async for entry in self._build_places():
            yield entry
        async for entry in self._build_files():
            yield entry

    async def _build_people(self) -> AsyncIterable[dict[str, str]]:
        for person in self._app.project.ancestry[Person]:
            entry = await self._build_person(person)
            if entry is not None:
                yield entry

    async def _build_places(self) -> AsyncIterable[dict[str, str]]:
        for place in self._app.project.ancestry[Place]:
            entry = await self._build_place(place)
            if entry is not None:
                yield entry

    async def _build_files(self) -> AsyncIterable[dict[str, str]]:
        for file in self._app.project.ancestry[File]:
            entry = await self._build_file(file)
            if entry is not None:
                yield entry

    async def _render_entity(self, entity: Entity) -> str:
        entity_type_name = get_entity_type_name(entity)
        return await self._app.jinja2_environment.select_template([
            f'search/result-{camel_case_to_snake_case(entity_type_name)}.html.j2',
            'search/result.html.j2',
        ]).render_async({
            'task_context': self._task_context,
            'localizer': self._localizer,
            'entity': entity,
        })

    async def _build_person(self, person: Person) -> dict[Any, Any] | None:
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
            'text': ' '.join(names),
            'result': await self._render_entity(person),
        }

    async def _build_place(self, place: Place) -> dict[Any, Any] | None:
        if place.private:
            return None

        return {
            'text': ' '.join(map(lambda x: x.name.lower(), place.names)),
            'result': await self._render_entity(place),
        }

    async def _build_file(self, file: File) -> dict[Any, Any] | None:
        if file.private:
            return None

        if not file.description:
            return None
        return {
            'text': file.description.lower(),
            'result': await self._render_entity(file),
        }
