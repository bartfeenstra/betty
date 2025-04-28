"""
URL generators for project resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final
from urllib.parse import quote, urlparse

from typing_extensions import override

from betty.media_type.media_types import HTML, JSON, JSON_LD
from betty.model import Entity
from betty.project.factory import ProjectDependentFactory
from betty.string import camel_case_to_kebab_case
from betty.typing import private
from betty.url import (
    InvalidMediaType,
    PassthroughUrlGenerator,
    UrlGenerator,
    generate_from_path,
)
from betty.url import (
    LocalizedUrlGenerator as StdLocalizedUrlGenerator,
)
from betty.url import (
    StaticUrlGenerator as StdStaticUrlGenerator,
)
from betty.url.proxy import ProxyLocalizedUrlGenerator, ProxyUrlGenerator
from betty.warnings import deprecated

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.ancestry import Ancestry
    from betty.locale import Localey
    from betty.media_type import MediaType
    from betty.project import Project


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

    def _generate_from_entity(
        self,
        entity: Entity,
        pattern: str,
        *,
        media_type: MediaType | None,
        locale: Localey | None,
        absolute: bool,
    ) -> str:
        if media_type not in [HTML, JSON_LD, JSON]:
            raise InvalidMediaType.new(entity, media_type)
        extension, locale = _get_extension_and_locale(
            media_type, self._default_locale, locale=locale
        )
        return self._generate_from_path(
            pattern.format(
                entity_type=camel_case_to_kebab_case(entity.plugin_id()),
                entity_id=quote(entity.id),
                extension=extension,
            ),
            absolute=absolute,
            locale=locale,
        )

    def _generate_from_entity_type(
        self,
        entity_type: type[Entity],
        pattern: str,
        *,
        media_type: MediaType | None,
        locale: Localey | None,
        absolute: bool,
    ) -> str:
        if media_type not in [HTML, JSON_LD, JSON]:
            raise InvalidMediaType.new(entity_type, media_type)
        extension, locale = _get_extension_and_locale(
            media_type, self._default_locale, locale=locale
        )
        return self._generate_from_path(
            pattern.format(
                entity_type=camel_case_to_kebab_case(entity_type.plugin_id()),
                extension=extension,
            ),
            absolute=absolute,
            locale=locale,
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


async def new_project_url_generator(project: Project) -> UrlGenerator:
    """
    Generate URLs for all resources provided by a Betty project.
    """
    entity_url_generator = await _EntityUrlGenerator.new_for_project(project)
    return ProxyUrlGenerator(
        await _EntityTypeUrlGenerator.new_for_project(project),
        entity_url_generator,
        _EntityUrlUrlGenerator(project.ancestry, entity_url_generator),
        await _LocalizedPathUrlUrlGenerator.new_for_project(project),
        await _StaticPathUrlUrlGenerator.new_for_project(project),
        PassthroughUrlGenerator(),
    )


@deprecated(
    f"This class has been deprecated since Betty 0.4.8, and will be removed in Betty 0.5. Instead use {new_project_url_generator}."
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
    if media_type in (JSON, JSON_LD):
        return "json", None
    raise ValueError(f'Unknown entity media type "{media_type}".')


class __EntityTypeUrlGenerator(_ProjectUrlGenerator):
    _pattern = "/{entity_type}/index.{extension}"

    def supports(self, resource: Any) -> bool:
        return isinstance(resource, type) and issubclass(resource, Entity)


@final
class _EntityTypeUrlGenerator(__EntityTypeUrlGenerator, UrlGenerator):
    @override
    def generate(
        self,
        resource: type[Entity],
        *,
        media_type: MediaType | None = None,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        return self._generate_from_entity_type(
            resource,
            self._pattern,
            media_type=media_type,
            locale=locale,
            absolute=absolute,
        )


@final
class _EntityTypeLocalizedUrlGenerator(
    __EntityTypeUrlGenerator, StdLocalizedUrlGenerator
):
    @override
    def generate(
        self,
        resource: type[Entity],
        media_type: MediaType,
        *,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        return self._generate_from_entity_type(
            resource,
            self._pattern,
            media_type=media_type,
            locale=locale,
            absolute=absolute,
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
        media_type: MediaType | None = None,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        return self._generate_from_entity(
            resource,
            self._pattern,
            media_type=media_type,
            locale=locale,
            absolute=absolute,
        )


@final
class _EntityLocalizedUrlGenerator(__EntityUrlGenerator, StdLocalizedUrlGenerator):
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
        return self._generate_from_entity(
            resource,
            self._pattern,
            media_type=media_type,
            locale=locale,
            absolute=absolute,
        )


class _EntityUrlUrlGenerator(UrlGenerator):
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
        *,
        media_type: MediaType | None = None,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        parsed_url = urlparse(resource)
        entity_type_id = parsed_url.netloc
        entity_id = parsed_url.path[1:]
        entity = self._ancestry[entity_type_id][entity_id]
        return self._entity_url_generator.generate(
            entity, media_type=media_type, absolute=absolute, locale=locale
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
        media_type: MediaType | None = None,
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
        media_type: MediaType | None = None,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert self.supports(resource)
        parsed_url = urlparse(resource)
        url_path = "/" + (parsed_url.netloc + parsed_url.path).lstrip("/")
        return self._generate_from_path(url_path, absolute=absolute)


@deprecated(
    f"This class has been deprecated since Betty 0.4.8, and will be removed in Betty 0.5. Instead use {UrlGenerator}."
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
        return cls(
            await _EntityTypeLocalizedUrlGenerator.new_for_project(project),
            await _EntityLocalizedUrlGenerator.new_for_project(project),
            await _LocalizedPathUrlGenerator.new_for_project(project),
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
