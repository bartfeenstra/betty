from os.path import dirname
from typing import Optional, Iterable, Callable, Dict

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

    def _index(self) -> Iterable:
        # Create the environment here, because doing so in the initializer would be at a time when not all plugins have
        # been initialized yet
        environment = create_environment(self._site)
        for person in self._site.ancestry.people.values():
            yield {
                'text': ('%s %s' % (person.individual_name, person.family_name)).lower(),
                'result': environment.get_template('search-result-person.html.j2').render({
                    'person': person,
                })
            }
        for place in self._site.ancestry.places.values():
            yield {
                'text': place.name.lower(),
                'result': environment.get_template('search-result-place.html.j2').render({
                    'place': place,
                })
            }

    @property
    def globals(self) -> Dict[str, Callable]:
        return {
            'search_index': self._index,
        }
