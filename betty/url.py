from __future__ import annotations
from contextlib import suppress
from typing import Any, Optional, Type

from betty.app import App
from betty.locale import negotiate_locale
from betty.model import Entity
from betty.model.ancestry import PersonName, Event, Place, File, Source, Citation, Note, Person
from betty.media_type import EXTENSIONS
from betty.project import ProjectConfiguration


class ContentNegotiationUrlGenerator:
    def generate(self, resource: Any, media_type: str, absolute: bool = False) -> str:
        raise NotImplementedError


class StaticUrlGenerator:
    def generate(self, resource: Any, absolute: bool = False, ) -> str:
        raise NotImplementedError


class ContentNegotiationPathUrlGenerator(ContentNegotiationUrlGenerator):
    def __init__(self, app: App):
        self._app = app

    def generate(self, resource: Any, media_type: str, absolute: bool = False) -> str:
        return _generate_from_path(self._app.project.configuration, resource, absolute, self._app.locale)


class StaticPathUrlGenerator(StaticUrlGenerator):
    def __init__(self, configuration: ProjectConfiguration):
        self._configuration = configuration

    def generate(self, resource: Any, absolute: bool = False, ) -> str:
        return _generate_from_path(self._configuration, resource, absolute)


class _EntityUrlGenerator(ContentNegotiationUrlGenerator):
    def __init__(self, app: App, entity_type: Type[Entity], pattern: str):
        self._app = app
        self._entity_type = entity_type
        self._pattern = pattern

    def generate(self, entity: Entity, media_type: str, absolute: bool = False) -> str:
        if not isinstance(entity, self._entity_type):
            raise ValueError('%s is not a %s' % (type(entity), self._entity_type))
        return _generate_from_path(self._app.project.configuration, self._pattern % (entity.id, EXTENSIONS[media_type]), absolute, self._app.locale)


class PersonNameUrlGenerator(ContentNegotiationUrlGenerator):
    def __init__(self, person_url_generator: ContentNegotiationUrlGenerator):
        self._person_url_generator = person_url_generator

    def generate(self, name: PersonName, media_type: str, absolute: bool = False) -> str:
        if not isinstance(name, PersonName):
            raise ValueError('%s is not a %s' % (type(name), PersonName))
        return self._person_url_generator.generate(name.person, media_type, absolute)


class AppUrlGenerator(ContentNegotiationUrlGenerator):
    def __init__(self, app: App):
        person_url_generator = _EntityUrlGenerator(app, Person, 'person/%s/index.%s')
        self._generators = [
            person_url_generator,
            PersonNameUrlGenerator(person_url_generator),
            _EntityUrlGenerator(app, Event, 'event/%s/index.%s'),
            _EntityUrlGenerator(app, Place, 'place/%s/index.%s'),
            _EntityUrlGenerator(app, File, 'file/%s/index.%s'),
            _EntityUrlGenerator(app, Source, 'source/%s/index.%s'),
            _EntityUrlGenerator(app, Citation, 'citation/%s/index.%s'),
            _EntityUrlGenerator(app, Note, 'note/%s/index.%s'),
            ContentNegotiationPathUrlGenerator(app),
        ]

    def generate(self, resource: Any, media_type: str, absolute: bool = False) -> str:
        for generator in self._generators:
            with suppress(ValueError):
                return generator.generate(resource, media_type, absolute)
        raise ValueError('No URL generator found for %s.' % (
            resource if isinstance(resource, str) else type(resource)))


def _generate_from_path(configuration: ProjectConfiguration, path: str, absolute: bool = False, locale: Optional[str] = None) -> str:
    if not isinstance(path, str):
        raise ValueError('%s is not a string.' % type(path))
    url = configuration.base_url if absolute else ''
    url += '/'
    if configuration.root_path:
        url += configuration.root_path + '/'
    if locale and configuration.multilingual:
        try:
            locale_configuration = configuration.locales[locale]
        except KeyError:
            project_locales = {
                locale_configuration.locale
                for locale_configuration
                in configuration.locales
            }
            try:
                locale_configuration = configuration.locales[negotiate_locale(
                    locale,
                    project_locales,
                )]
            except KeyError:
                raise ValueError(f'Cannot generate URLs in "{locale}", because it cannot be resolved to any of the enabled project locales: {", ".join(project_locales)}')
        url += locale_configuration.alias + '/'
    url += path.strip('/')
    if configuration.clean_urls and url.endswith('/index.html'):
        url = url[:-10]
    return url.rstrip('/')
