from typing import Any, Type, Optional

from betty.ancestry import Person, Citation, Source, File, Place, Event, Identifiable
from betty.config import Configuration
from betty.content_type import EXTENSIONS


class UrlGenerator:
    def generate(self, resource: Any, content_type: str, absolute: bool = False, locale: Optional[str] = None) -> str:
        raise NotImplementedError


class StaticUrlGenerator:
    def generate(self, resource: Any, absolute: bool = False, ) -> str:
        raise NotImplementedError


class PathResourceUrlGenerator(UrlGenerator):
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource, content_type, **kwargs) -> str:
        return _generate_from_path(self._configuration, resource, localize=True, **kwargs)


class StaticPathUrlGenerator(StaticUrlGenerator):
    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def generate(self, resource, **kwargs) -> str:
        return _generate_from_path(self._configuration, resource, localize=False, **kwargs)


class IdentifiableResourceUrlGenerator(UrlGenerator):
    def __init__(self, configuration: Configuration, identifiable_type: Type[Identifiable], pattern: str):
        self._configuration = configuration
        self._type = identifiable_type
        self._pattern = pattern

    def generate(self, resource: Identifiable, content_type, **kwargs) -> str:
        if not isinstance(resource, self._type):
            raise ValueError('%s is not a %s' % (type(resource), self._type))
        kwargs['localize'] = True
        return _generate_from_path(self._configuration, self._pattern % (resource.id, EXTENSIONS[content_type]), **kwargs)


class SiteUrlGenerator(UrlGenerator):
    def __init__(self, configuration: Configuration):
        self._generators = [
            IdentifiableResourceUrlGenerator(
                configuration, Person, 'person/%s/index.%s'),
            IdentifiableResourceUrlGenerator(
                configuration, Event, 'event/%s/index.%s'),
            IdentifiableResourceUrlGenerator(
                configuration, Place, 'place/%s/index.%s'),
            IdentifiableResourceUrlGenerator(
                configuration, File, 'file/%s/index.%s'),
            IdentifiableResourceUrlGenerator(
                configuration, Source, 'source/%s/index.%s'),
            IdentifiableResourceUrlGenerator(
                configuration, Citation, 'citation/%s/index.%s'),
            PathResourceUrlGenerator(configuration),
        ]

    def generate(self, resource: Any, *args, **kwargs) -> str:
        for generator in self._generators:
            try:
                return generator.generate(resource, *args, **kwargs)
            except ValueError:
                pass
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
