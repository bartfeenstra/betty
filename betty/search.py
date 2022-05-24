from typing import Dict, Iterable, Optional

from betty.model import get_entity_type_name
from betty.model.ancestry import Person, Place, File, Entity
from betty.app import App
from betty.string import camel_case_to_snake_case


class Index:
    def __init__(self, app: App):
        self._app = app

    def build(self) -> Iterable[Dict]:
        return filter(None, [
            *[self._build_person(person) for person in self._app.project.ancestry.entities[Person]],
            *[self._build_place(place) for place in self._app.project.ancestry.entities[Place]],
            *[self._build_file(file) for file in self._app.project.ancestry.entities[File]],
        ])

    def _render_entity(self, entity: Entity):
        entity_type_name = get_entity_type_name(entity.entity_type())
        return self._app.jinja2_environment.negotiate_template([
            f'search/result-{camel_case_to_snake_case(entity_type_name)}.html.j2',
            'search/result.html.j2',
        ]).render({
            'entity': entity,
        })

    def _build_person(self, person: Person) -> Optional[Dict]:
        if person.private:
            return
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

    def _build_place(self, place: Place) -> Optional[Dict]:
        return {
            'text': ' '.join(map(lambda x: x.name.lower(), place.names)),
            'result': self._render_entity(place),
        }

    def _build_file(self, file: File) -> Optional[Dict]:
        if file.description is not None:
            return {
                'text': file.description.lower(),
                'result': self._render_entity(file),
            }
