"""
URL generators for project resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final
from urllib.parse import urlparse

from typing_extensions import override

from betty.media_type.media_types import HTML, JSON, JSON_LD
from betty.model import Entity, EntityDefinition
from betty.project.factory import ProjectDependentFactory
from betty.string import camel_case_to_kebab_case
from betty.url import (
    InvalidMediaType,
    PassthroughUrlGenerator,
    UrlGenerator,
    generate_from_path,
)
from betty.url.proxy import ProxyUrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.ancestry import Ancestry
    from betty.locale import LocaleLike
    from betty.media_type import MediaType
    from betty.plugin import PluginRepository
    from betty.project import Project


class _ProjectUrlGenerator(ProjectDependentFactory):
    def __init__(
        self,
        base_url: str,
        root_path: str,
        locales_to_aliases: Mapping[str, str],
        clean_urls: bool,
        /,
    ):
        self._base_url = base_url
        self._root_path = root_path
        self._locales_to_aliases = locales_to_aliases
        assert len(locales_to_aliases)
        self._default_locale = next(iter(locales_to_aliases))
        self._clean_urls = clean_urls

    @override
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
        self,
        path: str,
        *,
        absolute: bool,
        fragment: str | None,
        locale: LocaleLike | None,
        query: Mapping[str, Sequence[str]] | None,
    ) -> str:
        return generate_from_path(
            path,
            absolute=absolute,
            base_url=self._base_url,
            clean_urls=self._clean_urls,
            fragment=fragment,
            locale=locale,
            locale_aliases=self._locales_to_aliases,
            query=query,
            root_path=self._root_path,
        )

    def _generate_from_entity(
        self,
        entity: Entity,
        pattern: str,
        *,
        absolute: bool,
        fragment: str | None,
        locale: LocaleLike | None,
        media_type: MediaType | None,
        query: Mapping[str, Sequence[str]] | None,
    ) -> str:
        if media_type not in [HTML, JSON_LD, JSON]:
            raise InvalidMediaType(entity, media_type)
        extension, locale = _get_extension_and_locale(
            media_type, self._default_locale, locale=locale
        )
        return self._generate_from_path(
            pattern.format(
                entity_type=camel_case_to_kebab_case(entity.plugin.id),
                entity_id=entity.public_id,
                extension=extension,
            ),
            absolute=absolute,
            fragment=fragment,
            locale=locale,
            query=query,
        )

    def _generate_from_entity_type(
        self,
        entity_type: EntityDefinition,
        pattern: str,
        *,
        absolute: bool,
        fragment: str | None,
        locale: LocaleLike | None,
        media_type: MediaType | None,
        query: Mapping[str, Sequence[str]] | None,
    ) -> str:
        if media_type not in [HTML, JSON_LD, JSON]:
            raise InvalidMediaType(entity_type, media_type)
        extension, locale = _get_extension_and_locale(
            media_type, self._default_locale, locale=locale
        )
        return self._generate_from_path(
            pattern.format(
                entity_type=camel_case_to_kebab_case(entity_type.id),
                extension=extension,
            ),
            absolute=absolute,
            fragment=fragment,
            locale=locale,
            query=query,
        )


async def new_project_url_generator(project: Project) -> UrlGenerator:
    """
    Generate URLs for all resources provided by a Betty project.
    """
    entity_url_generator = await _EntityUrlGenerator.new_for_project(project)
    return ProxyUrlGenerator(
        await _EntityTypeUrlGenerator.new_for_project(project),
        entity_url_generator,
        _EntityUrlUrlGenerator(
            project.ancestry,
            entity_url_generator,
            await project.plugins(EntityDefinition),
        ),
        await _LocalizedPathUrlUrlGenerator.new_for_project(project),
        await _StaticPathUrlUrlGenerator.new_for_project(project),
        PassthroughUrlGenerator(),
    )


def _get_extension_and_locale(
    media_type: MediaType, default_locale: str, *, locale: LocaleLike | None
) -> tuple[str, LocaleLike | None]:
    if media_type == HTML:
        return "html", locale or default_locale
    if media_type in (JSON, JSON_LD):
        return "json", None
    raise ValueError(f'Unknown entity media type "{media_type}".')


class __EntityTypeUrlGenerator(_ProjectUrlGenerator):
    _pattern = "/{entity_type}/index.{extension}"

    def supports(self, resource: Any) -> bool:
        return isinstance(resource, EntityDefinition)


@final
class _EntityTypeUrlGenerator(__EntityTypeUrlGenerator, UrlGenerator):
    @override
    def generate(
        self,
        resource: EntityDefinition,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: LocaleLike | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        assert self.supports(resource)
        return self._generate_from_entity_type(
            resource,
            self._pattern,
            absolute=absolute,
            fragment=fragment,
            locale=locale,
            media_type=media_type,
            query=query,
        )


class __EntityUrlGenerator(_ProjectUrlGenerator):
    _pattern = "/{entity_type}/{entity_id}/index.{extension}"

    def supports(self, resource: Any) -> bool:
        return isinstance(resource, Entity)


@final
class _EntityUrlGenerator(__EntityUrlGenerator, UrlGenerator):
    @override
    def generate(
        self,
        resource: Entity,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: LocaleLike | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        assert self.supports(resource)
        return self._generate_from_entity(
            resource,
            self._pattern,
            absolute=absolute,
            fragment=fragment,
            locale=locale,
            media_type=media_type,
            query=query,
        )


class _EntityUrlUrlGenerator(UrlGenerator):
    def __init__(
        self,
        ancestry: Ancestry,
        entity_url_generator: _EntityUrlGenerator,
        entity_types: PluginRepository[EntityDefinition],
    ):
        self._ancestry = ancestry
        self._entity_url_generator = entity_url_generator
        self._entity_types = entity_types

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
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: LocaleLike | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        parsed_url = urlparse(resource)
        entity_type_id = parsed_url.netloc
        entity_id = parsed_url.path[1:]
        entity = self._ancestry[self._entity_types[entity_type_id].cls][entity_id]
        return self._entity_url_generator.generate(
            entity,
            absolute=absolute,
            fragment=fragment,
            locale=locale,
            media_type=media_type,
            query=query,
        )


class _LocalizedPathUrlUrlGenerator(_ProjectUrlGenerator, UrlGenerator):
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
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: LocaleLike | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        assert self.supports(resource)
        parsed_url = urlparse(resource)
        url_path = "/" + (parsed_url.netloc + parsed_url.path).lstrip("/")
        return self._generate_from_path(
            url_path,
            absolute=absolute,
            fragment=fragment,
            locale=locale or self._default_locale,
            query=query,
        )


class _StaticPathUrlUrlGenerator(_ProjectUrlGenerator, UrlGenerator):
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
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: LocaleLike | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        assert self.supports(resource)
        parsed_url = urlparse(resource)
        url_path = "/" + (parsed_url.netloc + parsed_url.path).lstrip("/")
        return self._generate_from_path(
            url_path,
            absolute=absolute,
            fragment=fragment,
            locale=None,
            query=query,
        )
