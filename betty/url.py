from typing import Any, Type

from betty.ancestry import Person, Citation, Source, File, Place, Event, Identifiable
from betty.config import Configuration


class UrlGenerator:
    def generate(self, resource: Any, absolute: bool = False) -> str:
        raise NotImplementedError


class PathUrlGenerator(UrlGenerator):
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource: str, absolute: bool = False) -> str:
        if not isinstance(resource, str):
            raise ValueError('%s is not a string.' % type(resource))
        url = self._configuration.base_url if absolute else ''
        url += self._configuration.root_path
        url += resource.lstrip('/')
        if self._configuration.clean_urls and resource.endswith('/index.html'):
            url = url[:-10]
        return url


class AliasUrlGenerator(PathUrlGenerator):
    def __init__(self, configuration: Configuration, alias: str, path: str):
        PathUrlGenerator.__init__(self, configuration)
        self._alias = alias
        self._path = path

    def generate(self, resource: str, **kwargs) -> str:
        if resource != self._alias:
            raise ValueError('%s is not %s.' % (resource, self._alias))
        return PathUrlGenerator.generate(self, self._path, **kwargs)


class IdentifiableUrlGenerator(PathUrlGenerator):
    def __init__(self, configuration: Configuration, identifiable_type: Type[Identifiable], pattern: str):
        PathUrlGenerator.__init__(self, configuration)
        self._type = identifiable_type
        self._pattern = pattern

    def generate(self, resource: Identifiable, **kwargs) -> str:
        if not isinstance(resource, self._type):
            raise ValueError('%s is not a %s' % (type(resource), self._type))
        return PathUrlGenerator.generate(self, self._pattern % resource.id, **kwargs)


class DelegatingUrlGenerator(UrlGenerator):
    def __init__(self, configuration: Configuration):
        self._generators = []
        entity_types = [
            ('person', Person),
            ('event', Event),
            ('place', Place),
            ('file', File),
            ('source', Source),
            ('citation', Citation),
        ]
        for entity_type_name, entity_type in entity_types:
            self._generators += [
                AliasUrlGenerator(
                    configuration, '<%s>' % entity_type_name, '%s/index.html' % entity_type_name),
                IdentifiableUrlGenerator(
                    configuration, entity_type, '%s/%%s/index.html' % entity_type_name),
            ]
        self._generators += [
            AliasUrlGenerator(configuration, '<front>', '/index.html'),
            PathUrlGenerator(configuration),
        ]

    def generate(self, resource: Any, **kwargs) -> str:
        for generator in self._generators:
            try:
                return generator.generate(resource, **kwargs)
            except ValueError:
                pass
        raise ValueError('No URL generator found for %s.' % (
            resource if isinstance(resource, str) else type(resource)))
