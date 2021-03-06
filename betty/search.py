from typing import Dict, Iterable, Optional

from betty.ancestry import Person, Place, File, Resource
from betty.app import App


class Index:
    def __init__(self, app: App):
        self._app = app

    def build(self) -> Iterable[Dict]:
        return filter(None, [
            *[self._build_person(person) for person in self._app.ancestry.people.values()],
            *[self._build_place(place) for place in self._app.ancestry.places.values()],
            *[self._build_file(file) for file in self._app.ancestry.files.values()],
        ])

    def _render_resource(self, resource: Resource):
        return self._app.jinja2_environment.get_template('search/result-%s.html.j2' % resource.resource_type_name()).render({
            resource.resource_type_name(): resource,
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
                'result': self._render_resource(person),
            }

    def _build_place(self, place: Place) -> Optional[Dict]:
        return {
            'text': ' '.join(map(lambda x: x.name.lower(), place.names)),
            'result': self._render_resource(place),
        }

    def _build_file(self, file: File) -> Optional[Dict]:
        if file.description is not None:
            return {
                'text': file.description.lower(),
                'result': self._render_resource(file),
            }
