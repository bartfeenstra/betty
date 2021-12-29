from contextlib import suppress
from typing import Any, Optional, Type

from betty.model import Entity
from betty.model.ancestry import PersonName, Event, Place, File, Source, Citation, Note, Person
from betty.config import Configuration
from betty.media_type import EXTENSIONS


class LocalizedUrlGenerator:
    def generate(self, resource: Any, media_type: str, absolute: bool = False, locale: Optional[str] = None) -> str:
        raise NotImplementedError


class StaticUrlGenerator:
    def generate(self, resource: Any, absolute: bool = False, ) -> str:
        raise NotImplementedError


class LocalizedPathUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource, media_type, **kwargs) -> str:
        return _generate_from_path(self._configuration, resource, localize=True, **kwargs)


class StaticPathUrlGenerator(StaticUrlGenerator):
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource, **kwargs) -> str:
        return _generate_from_path(self._configuration, resource, localize=False, **kwargs)


class _EntityUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, configuration: Configuration, entity_type: Type[Entity], pattern: str):
        self._configuration = configuration
        self._entity_type = entity_type
        self._pattern = pattern

    def generate(self, entity: Entity, media_type, **kwargs) -> str:
        if not isinstance(entity, self._entity_type):
            raise ValueError('%s is not a %s' % (type(entity), self._entity_type))
        kwargs['localize'] = True
        return _generate_from_path(self._configuration, self._pattern % (entity.id, EXTENSIONS[media_type]), **kwargs)


class PersonNameUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, person_url_generator: LocalizedUrlGenerator):
        self._person_url_generator = person_url_generator

    def generate(self, name: PersonName, *args, **kwargs) -> str:
        if not isinstance(name, PersonName):
            raise ValueError('%s is not a %s' % (type(name), PersonName))
        return self._person_url_generator.generate(name.person, *args, **kwargs)


class AppUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, configuration: Configuration):
        person_url_generator = _EntityUrlGenerator(configuration, Person, 'person/%s/index.%s')
        self._generators = [
            person_url_generator,
            PersonNameUrlGenerator(person_url_generator),
            _EntityUrlGenerator(configuration, Event, 'event/%s/index.%s'),
            _EntityUrlGenerator(configuration, Place, 'place/%s/index.%s'),
            _EntityUrlGenerator(configuration, File, 'file/%s/index.%s'),
            _EntityUrlGenerator(configuration, Source, 'source/%s/index.%s'),
            _EntityUrlGenerator(configuration, Citation, 'citation/%s/index.%s'),
            _EntityUrlGenerator(configuration, Note, 'note/%s/index.%s'),
            LocalizedPathUrlGenerator(configuration),
        ]

    def generate(self, resource: Any, *args, **kwargs) -> str:
        for generator in self._generators:
            with suppress(ValueError):
                return generator.generate(resource, *args, **kwargs)
        raise ValueError('No URL generator found for %s.' % (
            resource if isinstance(resource, str) else type(resource)))


def _generate_from_path(configuration: Configuration, path: str, localize: bool = False, absolute: bool = False, locale: Optional[str] = None) -> str:
    if not isinstance(path, str):
        raise ValueError('%s is not a string.' % type(path))
    url = configuration.base_url if absolute else ''
    url += '/'
    if configuration.root_path:
        url += configuration.root_path + '/'
    if localize and configuration.multilingual:
        locale_configuration = configuration.locales.default if locale is None else configuration.locales[locale]
        url += locale_configuration.alias + '/'
    url += path.strip('/')
    if configuration.clean_urls and url.endswith('/index.html'):
        url = url[:-10]
    return url.rstrip('/')
