from typing import AsyncIterable, Dict

from jinja2 import Environment

from betty.ancestry import Person, Place, File
from betty.site import Site


async def index(site: Site, environment: Environment) -> AsyncIterable[Dict]:
    async def render_person_result(person: Person):
        return await environment.get_template('search/result-person.html.j2').render_async({
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
                'result': await render_person_result(person),
            }

    async def render_place_result(place: Place):
        return await environment.get_template('search/result-place.html.j2').render_async({
            'place': place,
        })

    for place in site.ancestry.places.values():
        yield {
            'text': ' '.join(map(lambda x: x.name.lower(), place.names)),
            'result': await render_place_result(place),
        }

    async def render_file_result(file: File):
        return await environment.get_template('search/result-file.html.j2').render_async({
            'file': file,
        })

    for place in site.ancestry.files.values():
        if place.description is not None:
            yield {
                'text': place.description.lower(),
                'result': await render_file_result(place),
            }
