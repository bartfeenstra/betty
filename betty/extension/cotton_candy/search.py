from __future__ import annotations

from typing import Iterable, Any

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

    async def build(self) -> Iterable[dict[str, str]]:
        return filter(None, [
            *[
                await self._build_person(person)
                for person
                in self._app.project.ancestry[Person]
                if person.public
            ],
            *[
                await self._build_place(place)
                for place
                in self._app.project.ancestry[Place]
            ],
            *[
                await self._build_file(file)
                for file
                in self._app.project.ancestry[File]
                if file.public
            ],
        ])

    async def _render_entity(self, entity: Entity) -> str:
        entity_type_name = get_entity_type_name(entity)
        return await self._app.jinja2_environment.negotiate_template([
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
        if names:
            return {
                'text': ' '.join(names),
                'result': await self._render_entity(person),
            }
        return None

    async def _build_place(self, place: Place) -> dict[Any, Any] | None:
        return {
            'text': ' '.join(map(lambda x: x.name.lower(), place.names)),
            'result': await self._render_entity(place),
        }

    async def _build_file(self, file: File) -> dict[Any, Any] | None:
        if file.description is not None:
            return {
                'text': file.description.lower(),
                'result': await self._render_entity(file),
            }
        return None
