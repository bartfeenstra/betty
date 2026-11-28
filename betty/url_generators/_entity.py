"""
Entity URL generators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.collections.mapping.dict import empty_frozen_dict
from betty.content_type import MissingContentType
from betty.content_types import html
from betty.url_generator import UrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.content_type import ContentTypeDefinition
    from betty.locale import ResolvableLocale
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
        content_type: ContentTypeDefinition | None = None,
        query: Mapping[str, Sequence[str]] = empty_frozen_dict,
    ) -> str:
        if content_type is None:
            raise MissingContentType()
        if content_type is html:
            if not locale:
                locale = self._path_url_generator.default_locale
        else:
            locale = None
        return self._path_url_generator.generate(
            self._pattern.format(
                extension=html.extension, **self._pattern_data(resource)
            ),
            absolute=absolute,
            fragment=fragment,
            locale=locale,
            query=query,
        )

    def _pattern_data(self, resource: ResourceT, /) -> Mapping[str, str]:
        return {}
