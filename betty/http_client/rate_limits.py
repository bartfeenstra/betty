"""
Rate limit implementations.
"""

from aiohttp.client_reqrep import ClientRequest
from typing_extensions import override

from betty.http_client.rate_limit import RateLimit, RateLimitDefinition
from betty.plugin import Plugin


@RateLimitDefinition("wikipedia-action-api")
class WikipediaActionApi(RateLimit, Plugin):
    """
    The Wikipedia Action API rate limit.

    See https://www.mediawiki.org/wiki/API:Action_API.
    """

    @override
    def match(self, request: ClientRequest) -> bool:
        return (
            request.url.scheme in ("http", "https")
            and request.url.host is not None
            and request.url.host.endswith(".wikipedia.org")
            and request.url.path == "/w/api.php"
        )

    @override
    @property
    def limit(self) -> tuple[int, int]:
        # https://www.mediawiki.org/wiki/API:Etiquette states there are no hard limits on the Wikimedia
        # Foundation-managed Action APIs. We've taken the limit of "200 requests per second" from
        # https://www.mediawiki.org/wiki/Wikimedia_REST_API#Terms_and_conditions instead.
        return 200, 1


@RateLimitDefinition("wikipedia-rest-api")
class WikipediaRestApi(RateLimit, Plugin):
    """
    The Wikipedia REST API rate limit.

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
