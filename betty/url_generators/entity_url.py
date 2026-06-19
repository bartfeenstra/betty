"""
Generate URLs for entity references formatted as betty-entity:// URLs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard, final, override
from urllib.parse import urlsplit

from betty.url_generator import UrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.entity.collection.pool import EntityPool
    from betty.locale import ResolvableLocale
    from betty.media_type import ResolvableMediaType
    from betty.url_generators.entity import EntityUrlGenerator


@final
class EntityUrlUrlGenerator(UrlGenerator[str]):
    """
    Generate URLs for entity references formatted as betty-entity:// URLs.
    """

    def __init__(
        self,
        ancestry: EntityPool,
        entity_url_generator: EntityUrlGenerator,
        /,
    ):
        self._ancestry = ancestry
        self._entity_url_generator = entity_url_generator

    @override
    def supports(self, resource: Any, /) -> TypeGuard[str]:
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
        /,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: ResolvableMediaType | None = None,
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
