from os.path import dirname
from typing import Optional, Iterable, Callable, Dict

from betty.ancestry import Person, Place
from betty.jinja2 import Jinja2Provider, create_environment
from betty.plugin import Plugin
from betty.plugins.js import Js, JsEntryPointProvider, JsPackageProvider
from betty.site import Site


class Search(Plugin, JsPackageProvider, JsEntryPointProvider, Jinja2Provider):
    def __init__(self, site: Site):
        self._site = site

    @classmethod
    def depends_on(cls):
        return {Js}

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site)

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)

    @property
    def globals(self) -> Dict[str, Callable]:
        return {
            'search_index': lambda: index(self._site),
        }


def index(site: Site) -> Iterable:
    # Create the environments here, because doing so in the initializer would be at a time when not all plugins have
    # been initialized yet
    environments = {}
    for locale in site.configuration.locales:
        environments[locale] = create_environment(site, locale)

    def render_person_result(locale: str, person: Person):
        return environments[locale].get_template('search-result-person.html.j2').render({
            'person': person,
        })
    for person in site.ancestry.people.values():
        if person.individual_name is None and person.family_name is None:
            continue
        yield {
            'text': ' '.join([name.lower() for name in [person.individual_name, person.family_name] if name is not None]),
            'results': {locale: render_person_result(locale, person) for locale in environments},
        }

    def render_place_result(locale: str, place: Place):
        return environments[locale].get_template('search-result-place.html.j2').render({
            'place': place,
        })
    for place in site.ancestry.places.values():
        yield {
            'text': ' '.join(map(lambda x: x.name.lower(), place.names)),
            'results': {locale: render_place_result(locale, place) for locale in environments},
        }
