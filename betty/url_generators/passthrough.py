"""
URL generators that pass through resources unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard, final, override
from urllib.parse import urlsplit

from betty.collections import _empty_frozen_mapping
from betty.url_generator import UrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.locale import ResolvableLocale
    from betty.media_type import ResolvableMediaType


@final
class PassthroughUrlGenerator(UrlGenerator[str]):
    """
    Returns resources verbatim if they are absolute URLs already.
    """

    @override
    def supports(self, resource: Any, /) -> TypeGuard[str]:
        if not isinstance(resource, str):
            return False
        try:
            return bool(urlsplit(resource).scheme)
        except ValueError:
            return False

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
        query: Mapping[str, Sequence[str]] = _empty_frozen_mapping,
    ) -> str:
        return resource
