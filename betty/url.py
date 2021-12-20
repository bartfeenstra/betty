from typing import Any, Type, Optional

from betty.ancestry import Person, File, Place, Identifiable, PersonName, IdentifiableSource, IdentifiableEvent, \
    IdentifiableCitation, Note
from betty.config import Configuration
from betty.media_type import EXTENSIONS


class LocalizedUrlGenerator:
    def generate(self, resource: Any, media_type: str, absolute: bool = False, locale: Optional[str] = None) -> str:
        raise NotImplementedError


class StaticUrlGenerator:
    def generate(self, resource: Any, absolute: bool = False, ) -> str:
        raise NotImplementedError


class TypedUrlGenerator:
    resource_type = NotImplemented


class LocalizedPathUrlGenerator(LocalizedUrlGenerator):
    resource_type = str

    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource, media_type, **kwargs) -> str:
        return _generate_from_path(self._configuration, resource, localize=True, **kwargs)


class StaticPathUrlGenerator(StaticUrlGenerator):
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource, **kwargs) -> str:
        return _generate_from_path(self._configuration, resource, localize=False, **kwargs)


class IdentifiableResourceUrlGenerator(LocalizedUrlGenerator, TypedUrlGenerator):
    def __init__(self, configuration: Configuration, resource_type: Type[Identifiable], pattern: str):
        self._configuration = configuration
        self.resource_type = resource_type
        self._pattern = pattern

    def generate(self, resource: Identifiable, media_type, **kwargs) -> str:
        kwargs['localize'] = True
        return _generate_from_path(self._configuration, self._pattern % (resource.id, EXTENSIONS[media_type]), **kwargs)


class _PersonNameUrlGenerator(LocalizedUrlGenerator, TypedUrlGenerator):
    resource_type = PersonName

    def __init__(self, person_url_generator: LocalizedUrlGenerator):
        self._person_url_generator = person_url_generator

    def generate(self, name: PersonName, *args, **kwargs) -> str:
        return self._person_url_generator.generate(name.person, *args, **kwargs)


class AppUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, configuration: Configuration):
        person_url_generator = IdentifiableResourceUrlGenerator(configuration, Person, 'person/%s/index.%s')
        self._generators = {url_generator.resource_type: url_generator for url_generator in [
            person_url_generator,
            _PersonNameUrlGenerator(person_url_generator),
            IdentifiableResourceUrlGenerator(configuration, IdentifiableEvent, 'event/%s/index.%s'),
            IdentifiableResourceUrlGenerator(configuration, Place, 'place/%s/index.%s'),
            IdentifiableResourceUrlGenerator(configuration, File, 'file/%s/index.%s'),
            IdentifiableResourceUrlGenerator(configuration, IdentifiableSource, 'source/%s/index.%s'),
            IdentifiableResourceUrlGenerator(configuration, IdentifiableCitation, 'citation/%s/index.%s'),
            IdentifiableResourceUrlGenerator(configuration, Note, 'note/%s/index.%s'),
            LocalizedPathUrlGenerator(configuration),
        ]}

    def generate(self, resource: Any, *args, **kwargs) -> str:
        try:
            return self._generators[type(resource)].generate(resource, *args, **kwargs)
        except KeyError:
            raise ValueError(f'No URL generator found for {resource if isinstance(resource, str) else type(resource)}.')


def _generate_from_path(configuration: Configuration, path: str, localize: bool = False, absolute: bool = False, locale: Optional[str] = None) -> str:
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
