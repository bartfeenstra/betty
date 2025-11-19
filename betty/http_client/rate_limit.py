"""
HTTP client rate limiting.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

from betty.concurrent import AsynchronizedLock, RateLimiter
from betty.locale.localizable import _
from betty.plugin import ClassedPluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.ordered import OrderedPluginDefinition
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import MutableMapping, Sequence

    from aiohttp.client_middlewares import ClientHandlerType
    from aiohttp.client_reqrep import ClientRequest, ClientResponse


@final
@threadsafe
class RateLimitMiddleware:
    """
    HTTP client middleware to rate-limit requests.
    """

    def __init__(self, limits: Sequence[RateLimit], /):
        self._preferred_limits_and_limiters = [
            (limit, RateLimiter(*limit.limit)) for limit in limits
        ]
        self._default_limits_and_limiters: MutableMapping[
            tuple[str, str | None, int | None], RateLimiter
        ] = {}
        self._lock = AsynchronizedLock.new_threadsafe()

    async def __call__(
        self, request: ClientRequest, handler: ClientHandlerType
    ) -> ClientResponse:
        """
        Call the middleware.
        """
        request_limiter = self._get_matching_limiter(request)
        if not request_limiter:
            request_limiter = await self._get_default_limiter(request)
        await request_limiter.wait()
        return await handler(request)

    def _get_matching_limiter(self, request: ClientRequest) -> RateLimiter | None:
        for limit, limiter in self._preferred_limits_and_limiters:
            if limit.match(request):
                return limiter
        return None

    async def _get_default_limiter(self, request: ClientRequest) -> RateLimiter:
        default_key = (request.url.scheme, request.url.host, request.url.port)
        async with self._lock:
            try:
                return self._default_limits_and_limiters[default_key]
            except KeyError:
                request_limiter = RateLimiter(99, 1)
                self._default_limits_and_limiters[default_key] = request_limiter
                return request_limiter


class RateLimit:
    """
    A rate limit for HTTP requests.
    """

    @abstractmethod
    def match(self, request: ClientRequest) -> bool:
        """
        Whether this limit matches the given request.
        """

    @property
    @abstractmethod
    def limit(self) -> tuple[int, int]:
        """
        The limit expressed as a 2-tuple of the maximum and the period (in seconds).
        """


@final
class RateLimitDefinition(OrderedPluginDefinition, ClassedPluginDefinition[RateLimit]):
    """
    A rate limit definition.

    Read more about :doc:`/development/plugin/http-rate-limit`.
    """

    plugin_type_cls = RateLimit
    type = PluginTypeDefinition(
        id="http-rate-limit",
        label=_("HTTP client rate limit"),
        discoveries=EntryPointDiscovery("betty.http_rate_limit"),
    )
