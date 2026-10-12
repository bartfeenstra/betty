"""
Entity URL generators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.collections.mapping.dict import empty_frozen_dict
from betty.media_type import (
    resolve_media_type,
)
from betty.media_types import html
from betty.url_generator import UrlGenerator
from betty.validators.media_type import is_media_type

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
        query: Mapping[str, Sequence[str]] = empty_frozen_dict,
    ) -> str:
        if media_type is None:
            raise ValueError("Missing media type")
        media_type = resolve_media_type(media_type)
        media_type = is_media_type(media_type, media_types=[html])
        if not locale:
            locale = self._path_url_generator.default_locale
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
