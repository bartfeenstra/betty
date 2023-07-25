from __future__ import annotations

from typing import Iterable, Any

from betty.app import App
from betty.model import get_entity_type_name, Entity
from betty.model.ancestry import Person, Place, File
from betty.string import camel_case_to_snake_case


class Index:
    def __init__(self, app: App):
        self._app = app

    def build(self) -> Iterable[dict[Any, Any]]:
        return filter(None, [
            *[self._build_person(person) for person in self._app.project.ancestry[Person]],
            *[self._build_place(place) for place in self._app.project.ancestry[Place]],
            *[self._build_file(file) for file in self._app.project.ancestry[File]],
        ])

    def _render_entity(self, entity: Entity) -> str:
        entity_type_name = get_entity_type_name(entity)
        return self._app.jinja2_environment.negotiate_template([
            f'search/result-{camel_case_to_snake_case(entity_type_name)}.html.j2',
            'search/result.html.j2',
        ]).render({
            'entity': entity,
        })

    def _build_person(self, person: Person) -> dict[Any, Any] | None:
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
                'result': self._render_entity(person),
            }
        return None

    def _build_place(self, place: Place) -> dict[Any, Any] | None:
        return {
            'text': ' '.join(map(lambda x: x.name.lower(), place.names)),
            'result': self._render_entity(place),
        }

    def _build_file(self, file: File) -> dict[Any, Any] | None:
        if file.description is not None:
            return {
                'text': file.description.lower(),
                'result': self._render_entity(file),
            }
        return None
