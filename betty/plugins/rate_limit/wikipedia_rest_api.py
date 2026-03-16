"""
The Wikipedia REST API rate limit.
"""

from typing import override

from aiohttp import ClientRequest

from betty.http_client.rate_limit import RateLimit, RateLimitDefinition
from betty.plugin import Plugin


@RateLimitDefinition("wikipedia-rest-api")
class WikipediaRestApi(RateLimit, Plugin):
    """
    .. plugin:: http-rate-limit:wikipedia-rest-api.

    See https://www.mediawiki.org/wiki/Wikimedia_REST_API#Terms_and_conditions.
    """

    @override
    def match(self, request: ClientRequest) -> bool:
        return (
            request.url.scheme in ("http", "https")
            and request.url.host is not None
            and request.url.host.endswith(".wikipedia.org")
            and request.url.path == "/api/rest_v1"
            or request.url.path.startswith("/api/rest_v1/")
        )

    @override
    @property
    def limit(self) -> tuple[int, int]:
        return 200, 1
