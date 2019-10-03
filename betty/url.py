from typing import Any

from betty.ancestry import Person, Citation, Source, File, Place, Event, Identifiable
from betty.config import Configuration


class UrlGenerator:
    def generate(self, resource: Any, absolute: bool = False) -> str:
        raise NotImplementedError


class PathUrlGenerator:
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource: str, absolute=False) -> str:
        url = self._configuration.base_url if absolute else ''
        url += self._configuration.root_path
        url += resource.lstrip('/')
        if self._configuration.clean_urls and resource.endswith('/index.html'):
            url = url[:-10]
        return url


class IdentifiableUrlGenerator(PathUrlGenerator):
    def __init__(self, configuration: Configuration, pattern: str):
        PathUrlGenerator.__init__(self, configuration)
        self._pattern = pattern

    def generate(self, resource: Identifiable, absolute: bool = False) -> str:
        return PathUrlGenerator.generate(self, self._pattern % resource.id, absolute)


class DelegatingUrlGenerator:
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource: Any, absolute: bool = False) -> str:
        _GENERATORS = {
            str: PathUrlGenerator(self._configuration),
            Person: IdentifiableUrlGenerator(self._configuration, 'person/%s/index.html'),
            Event: IdentifiableUrlGenerator(self._configuration, 'event/%s/index.html'),
            Place: IdentifiableUrlGenerator(self._configuration, 'place/%s/index.html'),
            File: IdentifiableUrlGenerator(self._configuration, 'file/%s/index.html'),
            Source: IdentifiableUrlGenerator(self._configuration, 'source/%s/index.html'),
            Citation: IdentifiableUrlGenerator(self._configuration, 'citation/%s/index.html'),
        }
        return _GENERATORS[type(resource)].generate(resource, absolute)
