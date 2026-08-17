"""
Entity URL generators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.collections import _empty_frozen_mapping
from betty.media_type import (
    MissingMediaType,
    match_media_type,
    resolve_media_type,
)
from betty.media_types.html import HTML
from betty.media_types.json import JSON
from betty.media_types.json_ld import JSON_LD
from betty.url_generator import UrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.locale import ResolvableLocale
    from betty.media_type import ResolvableMediaType
    from betty.url_generators.path import PathUrlGenerator


class _EntityUrlGenerator[ResourceT](UrlGenerator[ResourceT]):
    def __init__(self, path_url_generator: PathUrlGenerator, pattern: str, /):
        self._path_url_generator = path_url_generator
        self._pattern = pattern

    @final
    @override
    def generate(
        self,
        resource: ResourceT,
        /,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: ResolvableMediaType | None = None,
        query: Mapping[str, Sequence[str]] = _empty_frozen_mapping,
    ) -> str:
        if media_type is None:
            raise MissingMediaType()
        media_type = resolve_media_type(media_type)
        media_type = match_media_type(
            media_type, (HTML.media_type, JSON_LD.media_type, JSON.media_type)
        )
        if media_type == HTML:
            if not locale:
                locale = self._path_url_generator.default_locale
        else:
            locale = None
        return self._path_url_generator.generate(
            self._pattern.format(
                extension=media_type.extensions[0], **self._pattern_data(resource)
            ),
            absolute=absolute,
            fragment=fragment,
            locale=locale,
            query=query,
        )

    def _pattern_data(self, resource: ResourceT, /) -> Mapping[str, str]:
        return {}
