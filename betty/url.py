from contextlib import suppress
from typing import Any, Type, Optional

from betty.ancestry import Person, File, Place, Identifiable, PersonName, IdentifiableSource, IdentifiableEvent, \
    IdentifiableCitation
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


class IdentifiableResourceUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, configuration: Configuration, identifiable_type: Type[Identifiable], pattern: str):
        self._configuration = configuration
        self._type = identifiable_type
        self._pattern = pattern

    def generate(self, resource: Identifiable, media_type, **kwargs) -> str:
        if not isinstance(resource, self._type):
            raise ValueError('%s is not a %s' % (type(resource), self._type))
        kwargs['localize'] = True
        return _generate_from_path(self._configuration, self._pattern % (resource.id, EXTENSIONS[media_type]), **kwargs)


class PersonNameUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, person_url_generator: LocalizedUrlGenerator):
        self._person_url_generator = person_url_generator

    def generate(self, name: PersonName, *args, **kwargs) -> str:
        if not isinstance(name, PersonName):
            raise ValueError('%s is not a %s' % (type(name), PersonName))
        return self._person_url_generator.generate(name.person, *args, **kwargs)


class SiteUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, configuration: Configuration):
        person_url_generator = IdentifiableResourceUrlGenerator(configuration, Person, 'person/%s/index.%s')
        self._generators = [
            person_url_generator,
            PersonNameUrlGenerator(person_url_generator),
            IdentifiableResourceUrlGenerator(
                configuration, IdentifiableEvent, 'event/%s/index.%s'),
            IdentifiableResourceUrlGenerator(
                configuration, Place, 'place/%s/index.%s'),
            IdentifiableResourceUrlGenerator(
                configuration, File, 'file/%s/index.%s'),
            IdentifiableResourceUrlGenerator(
                configuration, IdentifiableSource, 'source/%s/index.%s'),
            IdentifiableResourceUrlGenerator(
                configuration, IdentifiableCitation, 'citation/%s/index.%s'),
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
    url += configuration.root_path
    if localize and configuration.multilingual:
        if locale is None:
            locale = configuration.default_locale
        url += configuration.locales[locale].alias + '/'
    url += path.lstrip('/')
    if configuration.clean_urls and (path.endswith('/index.html') or path == 'index.html'):
        url = url[:-10]
    return url
