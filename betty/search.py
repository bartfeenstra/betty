from typing import Iterable

from jinja2 import Environment

from betty.ancestry import Person, Place, File
from betty.site import Site


def index(site: Site, environment: Environment) -> Iterable:
    def render_person_result(person: Person):
        return environment.get_template('search/result-person.html.j2').render({
            'person': person,
        })

    for person in site.ancestry.people.values():
        if person.private:
            continue
        names = []
        for name in person.names:
            if name.individual is not None:
                names.append(name.individual.lower())
            if name.affiliation is not None:
                names.append(name.affiliation.lower())
        if names:
            yield {
                'text': ' '.join(names),
                'result': render_person_result(person),
            }

    def render_place_result(place: Place):
        return environment.get_template('search/result-place.html.j2').render({
            'place': place,
        })

    for place in site.ancestry.places.values():
        yield {
            'text': ' '.join(map(lambda x: x.name.lower(), place.names)),
            'result': render_place_result(place),
        }

    def render_file_result(file: File):
        return environment.get_template('search/result-file.html.j2').render({
            'file': file,
        })

    for place in site.ancestry.files.values():
        if place.description is not None:
            yield {
                'text': place.description.lower(),
                'result': render_file_result(place),
            }
