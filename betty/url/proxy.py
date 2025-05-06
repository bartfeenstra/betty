"""
Provide proxy URL generators.
"""

from typing import Any, final

from typing_extensions import override

from betty.locale import Localey
from betty.media_type import MediaType
from betty.url import UnsupportedResource, UrlGenerator


@final
class ProxyUrlGenerator(UrlGenerator):
    """
    Expose multiple other URL generators as one unified URL generator.
    """

    def __init__(self, *upstreams: UrlGenerator):
        self._upstreams = upstreams

    @override
    def supports(self, resource: Any) -> bool:
        return any(upstream.supports(resource) for upstream in self._upstreams)

    @override
    def generate(
        self,
        resource: Any,
        *,
        media_type: MediaType | None = None,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        for upstream in self._upstreams:
            if upstream.supports(resource):
                return upstream.generate(
                    resource, media_type=media_type, absolute=absolute, locale=locale
                )
        raise UnsupportedResource.new(resource)
