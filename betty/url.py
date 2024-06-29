"""
Provide a URL generation API.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override

from betty.locale import negotiate_locale, Localey, to_locale
from betty.model import get_entity_type_name, Entity
from betty.string import camel_case_to_kebab_case

if TYPE_CHECKING:
    from betty.project import ProjectConfiguration, Project


class LocalizedUrlGenerator:
    """
    Generate URLs for localizable resources.
    """

    def generate(
        self,
        resource: Any,
        media_type: str,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        """
        Generate a URL for a resource.
        """
        raise NotImplementedError(repr(self))


class StaticUrlGenerator:
    """
    Generate URLs for static (non-localizable) resources.
    """

    def generate(
        self,
        resource: Any,
        absolute: bool = False,
    ) -> str:
        """
        Generate a URL for a resource.
        """
        raise NotImplementedError(repr(self))


class LocalizedPathUrlGenerator(LocalizedUrlGenerator):
    """
    Generate URLs for localizable file paths.
    """

    def __init__(self, project: Project):
        self._project = project

    @override
    def generate(
        self,
        resource: Any,
        media_type: str,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        return _generate_from_path(
            self._project.configuration,
            resource,
            absolute,
            self._project.app.localizer.locale if locale is None else locale,
        )


class StaticPathUrlGenerator(StaticUrlGenerator):
    """
    Generate URLs for static (non-localized) file paths.
    """

    def __init__(self, configuration: ProjectConfiguration):
        self._configuration = configuration

    @override
    def generate(
        self,
        resource: Any,
        absolute: bool = False,
    ) -> str:
        return _generate_from_path(self._configuration, resource, absolute)


class _EntityUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, project: Project, entity_type: type[Entity]):
        self._project = project
        self._entity_type = entity_type
        self._pattern = f"{camel_case_to_kebab_case(get_entity_type_name(entity_type))}/{{entity_id}}/index.{{extension}}"

    @override
    def generate(
        self,
        resource: Entity,
        media_type: str,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        if not isinstance(resource, self._entity_type):
            raise ValueError("%s is not a %s" % (type(resource), self._entity_type))

        if media_type == "text/html":
            extension = "html"
            if locale is None:
                locale = self._project.app.localizer.locale
        elif media_type == "application/json":
            extension = "json"
            locale = None
        else:
            raise ValueError(f'Unknown entity media type "{media_type}".')

        return _generate_from_path(
            self._project.configuration,
            self._pattern.format(
                entity_id=quote(resource.id),
                extension=extension,
            ),
            absolute,
            locale,
        )


class ProjectUrlGenerator(LocalizedUrlGenerator):
    """
    Generate URLs for all resources provided by a Betty project.
    """

    def __init__(self, project: Project):
        self._generators = [
            *(
                _EntityUrlGenerator(project, entity_type)
                for entity_type in project.entity_types
            ),
            LocalizedPathUrlGenerator(project),
        ]

    @override
    def generate(
        self,
        resource: Any,
        media_type: str,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        for generator in self._generators:
            with suppress(ValueError):
                return generator.generate(resource, media_type, absolute, locale)
        raise ValueError(
            "No URL generator found for %s."
            % (resource if isinstance(resource, str) else type(resource))
        )


def _generate_from_path(
    configuration: ProjectConfiguration,
    path: str,
    absolute: bool = False,
    localey: Localey | None = None,
) -> str:
    url = configuration.base_url if absolute else ""
    url += "/"
    if configuration.root_path:
        url += configuration.root_path + "/"
    if localey and configuration.locales.multilingual:
        locale = to_locale(localey)
        try:
            locale_configuration = configuration.locales[locale]
        except KeyError:
            project_locales = list(configuration.locales)
            try:
                negotiated_locale_data = negotiate_locale(locale, project_locales)
                if negotiated_locale_data is None:
                    raise KeyError
                locale_configuration = configuration.locales[
                    to_locale(negotiated_locale_data)
                ]
            except KeyError:
                raise ValueError(
                    f'Cannot generate URLs in "{locale}", because it cannot be resolved to any of the enabled project locales: {", ".join(project_locales)}'
                ) from None
        url += locale_configuration.alias + "/"
    url += path.strip("/")
    if configuration.clean_urls and url.endswith("/index.html"):
        url = url[:-10]
    return url.rstrip("/")
