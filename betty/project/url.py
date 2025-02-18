"""
URL generators for project resources.
"""

from __future__ import annotations

from typing import final, Any, Self, TYPE_CHECKING
from urllib.parse import quote, urlparse

from typing_extensions import override

from betty.media_type.media_types import HTML, JSON, JSON_LD
from betty.project.factory import ProjectDependentFactory
from betty.string import camel_case_to_kebab_case
from betty.typing import private
from betty.url import (
    generate_from_path,
    LocalizedUrlGenerator as StdLocalizedUrlGenerator,
    StaticUrlGenerator as StdStaticUrlGenerator,
    PassthroughLocalizedUrlGenerator,
)
from betty.url.proxy import ProxyLocalizedUrlGenerator
from betty.model import Entity

if TYPE_CHECKING:
    from betty.ancestry import Ancestry
    from betty.media_type import MediaType
    from betty.project import Project
    from betty.locale import Localey
    from collections.abc import Mapping


class _ProjectUrlGenerator(ProjectDependentFactory):
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

    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        """
        Create a new instance using the given project.
        """
        return cls(
            project.configuration.base_url,
            project.configuration.root_path,
            {
                locale_configuration.locale: locale_configuration.alias
                for locale_configuration in project.configuration.locales.values()
            },
            project.configuration.clean_urls,
        )

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
class StaticUrlGenerator(_ProjectUrlGenerator, StdStaticUrlGenerator):
    """
    Generate URLs for static (non-localized) file paths.
    """

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


def _get_extension_and_locale(
    media_type: MediaType, default_locale: str, *, locale: Localey | None
) -> tuple[str, Localey | None]:
    if media_type == HTML:
        return "html", locale or default_locale
    elif media_type in (JSON, JSON_LD):
        return "json", None
    else:
        raise ValueError(f'Unknown entity media type "{media_type}".')


@final
class _EntityTypeUrlGenerator(_ProjectUrlGenerator, StdLocalizedUrlGenerator):
    _pattern = "/{entity_type}/index.{extension}"

    @override
    def supports(self, resource: Any) -> bool:
        return isinstance(resource, type) and issubclass(resource, Entity)

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
        extension, locale = _get_extension_and_locale(
            media_type, self._default_locale, locale=locale
        )
        return self._generate_from_path(
            self._pattern.format(
                entity_type=camel_case_to_kebab_case(resource.plugin_id()),
                extension=extension,
            ),
            absolute=absolute,
            locale=locale,
        )


@final
class _EntityUrlGenerator(_ProjectUrlGenerator, StdLocalizedUrlGenerator):
    _pattern = "/{entity_type}/{entity_id}/index.{extension}"

    @override
    def supports(self, resource: Any) -> bool:
        return isinstance(resource, Entity)

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
        extension, locale = _get_extension_and_locale(
            media_type, self._default_locale, locale=locale
        )
        return self._generate_from_path(
            self._pattern.format(
                entity_type=camel_case_to_kebab_case(resource.plugin_id()),
                entity_id=quote(resource.id),
                extension=extension,
            ),
            absolute=absolute,
            locale=locale,
        )


class _EntityUrlUrlGenerator(StdLocalizedUrlGenerator):
    def __init__(self, ancestry: Ancestry, entity_url_generator: _EntityUrlGenerator):
        self._ancestry = ancestry
        self._entity_url_generator = entity_url_generator

    @override
    def supports(self, resource: Any) -> bool:
        if not isinstance(resource, str):
            return False
        try:
            parsed_url = urlparse(resource)
        except ValueError:
            return False
        if parsed_url.scheme != "betty-entity":
            return False
        if not parsed_url.netloc:
            return False
        if not len(parsed_url.path) >= 2:
            return False
        return True

    @override
    def generate(
        self,
        resource: str,
        media_type: MediaType,
        *,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        parsed_url = urlparse(resource)
        entity_type_id = parsed_url.netloc
        entity_id = parsed_url.path[1:]
        entity = self._ancestry[entity_type_id][entity_id]
        return self._entity_url_generator.generate(
            entity, media_type, absolute=absolute, locale=locale
        )


class _LocalizedPathUrlUrlGenerator(_ProjectUrlGenerator, StdLocalizedUrlGenerator):
    @override
    def supports(self, resource: Any) -> bool:
        if not isinstance(resource, str):
            return False
        try:
            parsed_url = urlparse(resource)
        except ValueError:
            return False
        if parsed_url.scheme != "betty":
            return False
        if not parsed_url.netloc and not parsed_url.path:
            return False
        return True

    @override
    def generate(
        self,
        resource: str,
        media_type: MediaType,
        *,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        parsed_url = urlparse(resource)
        url_path = "/" + (parsed_url.netloc + parsed_url.path).lstrip("/")
        return self._generate_from_path(
            url_path,
            absolute=absolute,
            locale=locale or self._default_locale,
        )


class _StaticPathUrlUrlGenerator(_ProjectUrlGenerator, StdLocalizedUrlGenerator):
    @override
    def supports(self, resource: Any) -> bool:
        if not isinstance(resource, str):
            return False
        try:
            parsed_url = urlparse(resource)
        except ValueError:
            return False
        if parsed_url.scheme != "betty-static":
            return False
        if not parsed_url.netloc and not parsed_url.path:
            return False
        return True

    @override
    def generate(
        self,
        resource: str,
        media_type: MediaType,
        *,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        parsed_url = urlparse(resource)
        url_path = "/" + (parsed_url.netloc + parsed_url.path).lstrip("/")
        return self._generate_from_path(url_path, absolute=absolute)


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
        entity_url_generator = await _EntityUrlGenerator.new_for_project(project)
        return cls(
            await _EntityTypeUrlGenerator.new_for_project(project),
            entity_url_generator,
            _EntityUrlUrlGenerator(project.ancestry, entity_url_generator),
            await _LocalizedPathUrlUrlGenerator.new_for_project(project),
            await _StaticPathUrlUrlGenerator.new_for_project(project),
            await _LocalizedPathUrlGenerator.new_for_project(project),
            PassthroughLocalizedUrlGenerator(),
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
