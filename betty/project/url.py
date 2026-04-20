"""
URL generators for project resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final, override
from urllib.parse import urlsplit

from betty.entity import Entity, EntityDefinition
from betty.factory import Manufacturable
from betty.media_type.media_types import HTML, JSON, JSON_LD
from betty.project import Project
from betty.string import camel_case_to_kebab_case
from betty.url import (
    PassthroughUrlGenerator,
    UnsupportedMediaType,
    UrlGenerator,
    generate_from_path,
)
from betty.url.proxy import ProxyUrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from babel import Locale

    from betty.entity.collection.pool import EntityPool
    from betty.locale import ResolvableLocale
    from betty.media_type import MediaType


class _ProjectUrlGenerator(Manufacturable):
    def __init__(
        self,
        base_url: str,
        root_path: str,
        locales_to_slugs: Mapping[Locale, str],
        clean_urls: bool,
        /,
    ):
        self._base_url = base_url
        self._root_path = root_path
        self._locales_to_slugs = locales_to_slugs
        assert len(locales_to_slugs)
        self._default_locale = next(iter(locales_to_slugs))
        self._clean_urls = clean_urls

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        """
        Create a new instance using the given project.
        """
        return cls(
            project.base_url,
            project.root_path,
            {
                project_locale.locale: project_locale.slug
                for project_locale in project.locales
            },
            project.clean_urls,
        )

    def _generate_from_path(
        self,
        path: str,
        *,
        absolute: bool,
        fragment: str | None,
        locale: ResolvableLocale | None,
        query: Mapping[str, Sequence[str]] | None,
    ) -> str:
        return generate_from_path(
            path,
            absolute=absolute,
            base_url=self._base_url,
            clean_urls=self._clean_urls,
            fragment=fragment,
            locale=locale,
            locale_slugs=self._locales_to_slugs,
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
        locale: ResolvableLocale | None,
        media_type: MediaType | None,
        query: Mapping[str, Sequence[str]] | None,
    ) -> str:
        if media_type not in [HTML, JSON_LD, JSON]:
            raise UnsupportedMediaType(entity, media_type)
        extension, locale = _get_extension_and_locale(
            media_type, self._default_locale, locale=locale
        )
        return self._generate_from_path(
            pattern.format(
                entity_type=camel_case_to_kebab_case(entity.plugin().id),
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
        locale: ResolvableLocale | None,
        media_type: MediaType | None,
        query: Mapping[str, Sequence[str]] | None,
    ) -> str:
        if media_type not in [HTML, JSON_LD, JSON]:
            raise UnsupportedMediaType(entity_type, media_type)
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


async def new_project_url_generator(project: Project, /) -> UrlGenerator:
    """
    Generate URLs for all resources provided by a Betty project.
    """
    entity_url_generator = await _EntityUrlGenerator.new(project)
    return ProxyUrlGenerator(
        await _EntityTypeUrlGenerator.new(project),
        entity_url_generator,
        _EntityUrlUrlGenerator(project.ancestry, entity_url_generator),
        await _LocalizedPathUrlUrlGenerator.new(project),
        await _StaticPathUrlUrlGenerator.new(project),
        PassthroughUrlGenerator(),
    )


def _get_extension_and_locale(
    media_type: MediaType, default_locale: Locale, *, locale: ResolvableLocale | None
) -> tuple[str, ResolvableLocale | None]:
    if media_type == HTML:
        return "html", locale or default_locale
    if media_type in (JSON, JSON_LD):
        return "json", None
    raise ValueError(f'Unknown entity media type "{media_type}".')


class __EntityTypeUrlGenerator(_ProjectUrlGenerator):
    _pattern = "/{entity_type}/index.{extension}"

    def supports(self, resource: Any, /) -> bool:
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
        locale: ResolvableLocale | None = None,
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

    def supports(self, resource: Any, /) -> bool:
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
        locale: ResolvableLocale | None = None,
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
        ancestry: EntityPool,
        entity_url_generator: _EntityUrlGenerator,
        /,
    ):
        self._ancestry = ancestry
        self._entity_url_generator = entity_url_generator

    @override
    def supports(self, resource: Any, /) -> bool:
        if not isinstance(resource, str):
            return False
        try:
            url_parts = urlsplit(resource)
        except ValueError:
            return False
        if url_parts.scheme != "betty-entity":
            return False
        if not url_parts.netloc:
            return False
        return len(url_parts.path) >= 2

    @override
    def generate(
        self,
        resource: str,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        url_parts = urlsplit(resource)
        entity_type_id = url_parts.netloc
        entity_id = url_parts.path[1:]
        entity = self._ancestry[entity_type_id][entity_id]
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
    def supports(self, resource: Any, /) -> bool:
        if not isinstance(resource, str):
            return False
        try:
            url_parts = urlsplit(resource)
        except ValueError:
            return False
        if url_parts.scheme != "betty":
            return False
        return not (not url_parts.netloc and not url_parts.path)

    @override
    def generate(
        self,
        resource: str,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        assert self.supports(resource)
        url_parts = urlsplit(resource)
        url_path = "/" + (url_parts.netloc + url_parts.path).lstrip("/")
        return self._generate_from_path(
            url_path,
            absolute=absolute,
            fragment=fragment,
            locale=locale or self._default_locale,
            query=query,
        )


class _StaticPathUrlUrlGenerator(_ProjectUrlGenerator, UrlGenerator):
    @override
    def supports(self, resource: Any, /) -> bool:
        if not isinstance(resource, str):
            return False
        try:
            url_parts = urlsplit(resource)
        except ValueError:
            return False
        if url_parts.scheme != "betty-static":
            return False
        return not (not url_parts.netloc and not url_parts.path)

    @override
    def generate(
        self,
        resource: str,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        assert self.supports(resource)
        url_parts = urlsplit(resource)
        url_path = "/" + (url_parts.netloc + url_parts.path).lstrip("/")
        return self._generate_from_path(
            url_path,
            absolute=absolute,
            fragment=fragment,
            locale=None,
            query=query,
        )
