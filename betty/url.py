from typing import Any, Type, Optional

from betty.ancestry import Person, Citation, Source, File, Place, Event, Identifiable
from betty.config import Configuration


class UrlGenerator:
    def generate(self, resource: Any, absolute: bool = False, locale: Optional[str] = None) -> str:
        raise NotImplementedError


class LocalizedPathUrlGenerator(UrlGenerator):
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource, **kwargs) -> str:
        return _generate_from_path(self._configuration, resource, localize=True, **kwargs)


class StaticPathUrlGenerator(UrlGenerator):
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource, **kwargs) -> str:
        return _generate_from_path(self._configuration, resource, localize=False, **kwargs)


class IdentifiableUrlGenerator(UrlGenerator):
    def __init__(self, configuration: Configuration, identifiable_type: Type[Identifiable], pattern: str):
        self._configuration = configuration
        self._type = identifiable_type
        self._pattern = pattern

    def generate(self, resource: Identifiable, **kwargs) -> str:
        if not isinstance(resource, self._type):
            raise ValueError('%s is not a %s' % (type(resource), self._type))
        kwargs['localize'] = True
        return _generate_from_path(self._configuration, self._pattern % resource.id, **kwargs)


# @todo We don't want a localize parameter, because any static URL must not be localized, and all other URLs must be.
# @todo In render_file(), strip the locale alias again like we experimented with before.
# @todo
# @todo


class LocalizedUrlGenerator(UrlGenerator):
    def __init__(self, configuration: Configuration):
        self._generators = [
            IdentifiableUrlGenerator(
                configuration, Person, 'person/%s/index.html'),
            IdentifiableUrlGenerator(
                configuration, Event, 'event/%s/index.html'),
            IdentifiableUrlGenerator(
                configuration, Place, 'place/%s/index.html'),
            IdentifiableUrlGenerator(
                configuration, File, 'file/%s/index.html'),
            IdentifiableUrlGenerator(
                configuration, Source, 'source/%s/index.html'),
            IdentifiableUrlGenerator(
                configuration, Citation, 'citation/%s/index.html'),
            LocalizedPathUrlGenerator(configuration),
        ]

    def generate(self, resource: Any, **kwargs) -> str:
        for generator in self._generators:
            try:
                return generator.generate(resource, **kwargs)
            except ValueError:
                pass
        raise ValueError('No URL generator found for %s.' % (
            resource if isinstance(resource, str) else type(resource)))


def _generate_from_path(configuration: Configuration, resource: str, localize: bool = False, absolute: bool = False, locale: Optional[str] = None) -> str:
    if not isinstance(resource, str):
        raise ValueError('%s is not a string.' % type(resource))
    url = configuration.base_url if absolute else ''
    url += configuration.root_path
    if localize and configuration.multilingual:
        if locale is None:
            locale = configuration.default_locale
        url += configuration.locales[locale].alias + '/'
    url += resource.lstrip('/')
    if configuration.clean_urls and resource.endswith('/index.html'):
        url = url[:-10]
    return url
