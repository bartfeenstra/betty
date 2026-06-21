"""
Provide proxy URL generators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.url import UnsupportedResource, UrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.locale import ResolvableLocale
    from betty.media_type import ResolvableMediaType


@final
class ProxyUrlGenerator(UrlGenerator):
    """
    Expose multiple other URL generators as one unified URL generator.
    """

    def __init__(self, *upstreams: UrlGenerator):
        self._upstreams = upstreams

    @override
    def supports(self, resource: Any, /) -> bool:
        return any(upstream.supports(resource) for upstream in self._upstreams)

    @override
    def generate(
        self,
        resource: Any,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: ResolvableMediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        for upstream in self._upstreams:
            if upstream.supports(resource):
                return upstream.generate(
                    resource,
                    absolute=absolute,
                    fragment=fragment,
                    locale=locale,
                    media_type=media_type,
                    query=query,
                )
        raise UnsupportedResource(resource)
