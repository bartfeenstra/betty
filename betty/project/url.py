"""
URL generators for project resources.
"""

from __future__ import annotations

from typing import final, Any, Self, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override

from betty import model
from betty.media_type.media_types import HTML, JSON, JSON_LD
from betty.project.factory import ProjectDependentFactory
from betty.string import camel_case_to_kebab_case
from betty.typing import private
from betty.url import (
    generate_from_path,
    LocalizedUrlGenerator as StdLocalizedUrlGenerator,
    StaticUrlGenerator as StdStaticUrlGenerator,
)
from betty.url.proxy import ProxyLocalizedUrlGenerator

if TYPE_CHECKING:
    from betty.media_type import MediaType
    from betty.project import Project
    from betty.model import Entity
    from betty.locale import Localey
    from collections.abc import Mapping


class _ProjectUrlGenerator:
    def __init__(
        self,
        base_url: str,
        root_path: str,
        locales: Mapping[str, str],
        clean_urls: bool,
    ):
        self._base_url = base_url
        self._root_path = root_path
        self._locales = locales
        assert len(locales)
        self._default_locale = next(iter(locales))
        self._clean_urls = clean_urls

    def _generate_from_path(
        self, path: str, *, absolute: bool = False, locale: Localey | None = None
    ) -> str:
        return generate_from_path(
            path,
            absolute=absolute,
            locale=locale,
            base_url=self._base_url,
            root_path=self._root_path,
            locales=self._locales,
            clean_urls=self._clean_urls,
        )


def _supports_path(resource: Any) -> bool:
    return isinstance(resource, str) and resource.startswith("/")


@final
class _LocalizedPathUrlGenerator(_ProjectUrlGenerator, StdLocalizedUrlGenerator):
    @override
    def supports(self, resource: Any) -> bool:
        return _supports_path(resource)

    @override
    def generate(
        self,
        resource: Any,
        media_type: MediaType,
        *,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        return self._generate_from_path(
            resource,
            absolute=absolute,
            locale=locale or self._default_locale,
        )


@final
class StaticUrlGenerator(
    ProjectDependentFactory, _ProjectUrlGenerator, StdStaticUrlGenerator
):
    """
    Generate URLs for static (non-localized) file paths.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(
            project.configuration.base_url,
            project.configuration.root_path,
            {
                locale_configuration.locale: locale_configuration.alias
                for locale_configuration in project.configuration.locales.values()
            },
            project.configuration.clean_urls,
        )

    @override
    def supports(self, resource: Any) -> bool:
        return _supports_path(resource)

    @override
    def generate(
        self,
        resource: Any,
        *,
        absolute: bool = False,
    ) -> str:
        assert self.supports(resource)
        return self._generate_from_path(resource, absolute=absolute)


class _EntityTypeDependentUrlGenerator(_ProjectUrlGenerator, StdLocalizedUrlGenerator):
    _pattern_pattern: str

    def __init__(
        self,
        base_url: str,
        root_path: str,
        locales: Mapping[str, str],
        clean_urls: bool,
        entity_type: type[Entity],
    ):
        super().__init__(base_url, root_path, locales, clean_urls)
        self._entity_type = entity_type
        self._pattern = self._pattern_pattern.format(
            entity_type=camel_case_to_kebab_case(entity_type.plugin_id())
        )

    def _get_extension_and_locale(
        self, media_type: MediaType, *, locale: Localey | None
    ) -> tuple[str, Localey | None]:
        if media_type == HTML:
            return "html", locale or self._default_locale
        elif media_type in (JSON, JSON_LD):
            return "json", None
        else:
            raise ValueError(f'Unknown entity media type "{media_type}".')


@final
class _EntityTypeUrlGenerator(_EntityTypeDependentUrlGenerator):
    _pattern_pattern = "/{entity_type}/index.{{extension}}"

    @override
    def supports(self, resource: Any) -> bool:
        return resource is self._entity_type

    @override
    def generate(
        self,
        resource: Entity,
        media_type: MediaType,
        *,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        extension, locale = self._get_extension_and_locale(media_type, locale=locale)
        return self._generate_from_path(
            self._pattern.format(
                extension=extension,
            ),
            absolute=absolute,
            locale=locale,
        )


@final
class _EntityUrlGenerator(_EntityTypeDependentUrlGenerator):
    _pattern_pattern = "/{entity_type}/{{entity_id}}/index.{{extension}}"

    @override
    def supports(self, resource: Any) -> bool:
        return isinstance(resource, self._entity_type)

    @override
    def generate(
        self,
        resource: Entity,
        media_type: MediaType,
        *,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        extension, locale = self._get_extension_and_locale(media_type, locale=locale)
        return self._generate_from_path(
            self._pattern.format(
                entity_id=quote(resource.id),
                extension=extension,
            ),
            absolute=absolute,
            locale=locale,
        )


@final
class LocalizedUrlGenerator(StdLocalizedUrlGenerator, ProjectDependentFactory):
    """
    Generate URLs for all resources provided by a Betty project.
    """

    @private
    def __init__(
        self,
        *upstreams: StdLocalizedUrlGenerator,
    ):
        self._upstream = ProxyLocalizedUrlGenerator(*upstreams)

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        args = (
            project.configuration.base_url,
            project.configuration.root_path,
            {
                locale_configuration.locale: locale_configuration.alias
                for locale_configuration in project.configuration.locales.values()
            },
            project.configuration.clean_urls,
        )
        return cls(
            *(
                _EntityTypeUrlGenerator(*args, entity_type)
                for entity_type in await model.ENTITY_TYPE_REPOSITORY.select()
            ),
            *(
                _EntityUrlGenerator(*args, entity_type)
                for entity_type in await model.ENTITY_TYPE_REPOSITORY.select()
            ),
            _LocalizedPathUrlGenerator(*args),
        )

    @override
    def supports(self, resource: Any) -> bool:
        return self._upstream.supports(resource)

    @override
    def generate(
        self,
        resource: Any,
        media_type: MediaType,
        *,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        return self._upstream.generate(
            resource, media_type, absolute=absolute, locale=locale
        )
