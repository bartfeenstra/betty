"""
Generate URLs for URL paths formatted as betty:// URLs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard, final, override
from urllib.parse import urlsplit

from betty.url_generator import UrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.locale import ResolvableLocale
    from betty.media_type import ResolvableMediaType
    from betty.url_generators.path import PathUrlGenerator


@final
class LocalizedPathUrlUrlGenerator(UrlGenerator[str]):
    """
    Generate URLs for URL paths formatted as betty:// URLs.
    """

    def __init__(self, path_url_generator: PathUrlGenerator, /):
        self._path_url_generator = path_url_generator

    @override
    def supports(self, resource: Any, /) -> TypeGuard[str]:
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
        /,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: ResolvableMediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        url_parts = urlsplit(resource)
        url_path = "/" + (url_parts.netloc + url_parts.path).lstrip("/")
        return self._path_url_generator.generate(
            url_path,
            absolute=absolute,
            fragment=fragment,
            locale=locale or self._path_url_generator.default_locale,
            media_type=media_type,
            query=query,
        )
