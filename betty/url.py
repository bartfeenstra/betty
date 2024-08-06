"""
Provide a URL generation API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING, final
from urllib.parse import quote

from betty import model
from betty.asyncio import wait_to_thread
from betty.locale import negotiate_locale, Localey, to_locale
from betty.string import camel_case_to_kebab_case
from typing_extensions import override

if TYPE_CHECKING:
    from betty.model import Entity
    from betty.project import ProjectConfiguration, Project


class _UrlGenerator(ABC):
    """
    Generate URLs for localizable resources.
    """

    @abstractmethod
    def supports(self, resource: Any) -> bool:
        """
        Whether the given resource is supported by this URL generator.
        """
        pass


class LocalizedUrlGenerator(_UrlGenerator):
    """
    Generate URLs for localizable resources.
    """

    @abstractmethod
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
        pass


class StaticUrlGenerator(_UrlGenerator):
    """
    Generate URLs for static (non-localizable) resources.
    """

    @abstractmethod
    def generate(
        self,
        resource: Any,
        absolute: bool = False,
    ) -> str:
        """
        Generate a URL for a resource.
        """
        pass


@final
class LocalizedPathUrlGenerator(LocalizedUrlGenerator):
    """
    Generate URLs for localizable file paths.
    """

    def __init__(self, project: Project):
        self._project = project

    @override
    def supports(self, resource: Any) -> bool:
        return isinstance(resource, str)

    @override
    def generate(
        self,
        resource: Any,
        media_type: str,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        return _generate_from_path(
            self._project.configuration,
            resource,
            absolute,
            self._project.app.localizer.locale if locale is None else locale,
        )


@final
class StaticPathUrlGenerator(StaticUrlGenerator):
    """
    Generate URLs for static (non-localized) file paths.
    """

    def __init__(self, configuration: ProjectConfiguration):
        self._configuration = configuration

    @override
    def supports(self, resource: Any) -> bool:
        return isinstance(resource, str)

    @override
    def generate(
        self,
        resource: Any,
        absolute: bool = False,
    ) -> str:
        assert self.supports(resource)
        return _generate_from_path(self._configuration, resource, absolute)


@final
class _EntityUrlGenerator(LocalizedUrlGenerator):
    def __init__(self, project: Project, entity_type: type[Entity]):
        self._project = project
        self._entity_type = entity_type
        self._pattern = f"{camel_case_to_kebab_case(entity_type.plugin_id())}/{{entity_id}}/index.{{extension}}"

    @override
    def supports(self, resource: Any) -> bool:
        return isinstance(resource, self._entity_type)

    @override
    def generate(
        self,
        resource: Entity,
        media_type: str,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)

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


@final
class ProjectUrlGenerator(LocalizedUrlGenerator):
    """
    Generate URLs for all resources provided by a Betty project.
    """

    def __init__(self, project: Project):
        self._generators = [
            *(
                _EntityUrlGenerator(project, entity_type)
                for entity_type in wait_to_thread(model.ENTITY_TYPE_REPOSITORY.select())
            ),
            LocalizedPathUrlGenerator(project),
        ]

    def _generator(self, resource: Any) -> LocalizedUrlGenerator | None:
        for generator in self._generators:
            if generator.supports(resource):
                return generator
        return None

    @override
    def supports(self, resource: Any) -> bool:
        return self._generator(resource) is not None

    @override
    def generate(
        self,
        resource: Any,
        media_type: str,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        generator = self._generator(resource)
        assert generator is not None
        return generator.generate(resource, media_type, absolute, locale)


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
