from __future__ import annotations

from contextlib import suppress
from typing import Any, Type, Set, cast

from betty.app import App
from betty.locale import negotiate_locale, Localey, to_locale
from betty.media_type import EXTENSIONS
from betty.model import get_entity_type_name, UserFacingEntity
from betty.project import ProjectConfiguration
from betty.string import camel_case_to_kebab_case


class ContentNegotiationUrlGenerator:
    def generate(self, resource: Any, media_type: str, absolute: bool = False, locale: Localey | None = None) -> str:
        raise NotImplementedError


class StaticUrlGenerator:
    def generate(self, resource: Any, absolute: bool = False, ) -> str:
        raise NotImplementedError


class ContentNegotiationPathUrlGenerator(ContentNegotiationUrlGenerator):
    def __init__(self, app: App):
        self._app = app

    def generate(self, resource: Any, media_type: str, absolute: bool = False, locale: Localey | None = None) -> str:
        return _generate_from_path(
            self._app.project.configuration,
            resource,
            absolute,
            self._app.locale if locale is None else locale,
        )


class StaticPathUrlGenerator(StaticUrlGenerator):
    def __init__(self, configuration: ProjectConfiguration):
        self._configuration = configuration

    def generate(self, resource: Any, absolute: bool = False, ) -> str:
        return _generate_from_path(self._configuration, resource, absolute)


class _EntityUrlGenerator(ContentNegotiationUrlGenerator):
    def __init__(self, app: App, entity_type: Type[UserFacingEntity]):
        self._app = app
        self._entity_type = entity_type
        self._pattern = f'{camel_case_to_kebab_case(get_entity_type_name(entity_type))}/{{entity_id}}/index.{{extension}}'

    def generate(self, entity: UserFacingEntity, media_type: str, absolute: bool = False, locale: Localey | None = None) -> str:
        if not isinstance(entity, self._entity_type):
            raise ValueError('%s is not a %s' % (type(entity), self._entity_type))
        return _generate_from_path(
            self._app.project.configuration,
            self._pattern.format(
                entity_id=entity.id,
                extension=EXTENSIONS[media_type],
            ),
            absolute,
            self._app.locale if locale is None else locale,
        )


class AppUrlGenerator(ContentNegotiationUrlGenerator):
    def __init__(self, app: App):
        self._generators = [
            *(
                _EntityUrlGenerator(app, entity_type)
                for entity_type in app.entity_types
                if issubclass(entity_type, UserFacingEntity)
            ),
            ContentNegotiationPathUrlGenerator(app),
        ]

    def generate(self, resource: Any, media_type: str, absolute: bool = False, locale: Localey | None = None) -> str:
        for generator in self._generators:
            with suppress(ValueError):
                return generator.generate(resource, media_type, absolute, locale)
        raise ValueError('No URL generator found for %s.' % (
            resource if isinstance(resource, str) else type(resource)))


def _generate_from_path(configuration: ProjectConfiguration, path: str, absolute: bool = False, localey: Localey | None = None) -> str:
    if not isinstance(path, str):
        raise ValueError('%s is not a string.' % type(path))
    url = configuration.base_url if absolute else ''
    url += '/'
    if configuration.root_path:
        url += configuration.root_path + '/'
    if localey and configuration.multilingual:
        locale = to_locale(localey)
        try:
            locale_configuration = configuration.locales[locale]
        except KeyError:
            project_locales = {
                locale_configuration.locale
                for locale_configuration
                in configuration.locales
            }
            try:
                negotiated_locale_data = negotiate_locale(locale, cast(Set[Localey], project_locales))
                if negotiated_locale_data is None:
                    raise KeyError
                locale_configuration = configuration.locales[to_locale(negotiated_locale_data)]
            except KeyError:
                raise ValueError(f'Cannot generate URLs in "{locale}", because it cannot be resolved to any of the enabled project locales: {", ".join(project_locales)}')
        url += locale_configuration.alias + '/'
    url += path.strip('/')
    if configuration.clean_urls and url.endswith('/index.html'):
        url = url[:-10]
    return url.rstrip('/')
