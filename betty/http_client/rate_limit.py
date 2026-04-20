"""
HTTP client rate limiting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.concurrent import RateLimiter, ThreadSafeLock
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import OrderedPluginDefinition
from betty.typing import threadsafe

if TYPE_CHECKING:
    import re
    from collections.abc import Iterable, MutableMapping

    from aiohttp.client_middlewares import ClientHandlerType
    from aiohttp.client_reqrep import ClientRequest, ClientResponse

    from betty.machine_name import ResolvableMachineName
    from betty.plugin.ordered import Order
    from betty.requirement import Requires


@final
@threadsafe
class RateLimitMiddleware:
    """
    HTTP client middleware to rate-limit requests.
    """

    def __init__(self, limits: Iterable[RateLimitDefinition], /):
        self._preferred_limits_and_limiters = [
            (limit, RateLimiter(*limit.limit)) for limit in limits
        ]
        self._default_limits_and_limiters: MutableMapping[
            tuple[str, str | None, int | None], RateLimiter
        ] = {}
        self._lock = ThreadSafeLock()

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


@final
@PluginTypeDefinition(
    "http-rate-limit",
    label=_("HTTP client rate limit"),
    label_plural=_("HTTP client rate limits"),
    label_countable=ngettext(
        "{count} HTTP client rate limit", "{count} HTTP client rate limits"
    ),
    description=_(
        "Rate limits ensure that Betty's HTTP client does not make more requests to a web service than that service supports or allows, by enforcing a maximum number of requests per timeframe."
    ),
)
class RateLimitDefinition(OrderedPluginDefinition):
    """
    .. plugin_type:: http-rate-limit.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        limit: tuple[int, int],
        match: str | re.Pattern,
        after: Order[RateLimitDefinition] = (),
        before: Order[RateLimitDefinition] = (),
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id, after=after, auto=True, before=before, requires=requires
        )
        self._limit = limit
        self._match = match

    @property
    def limit(self) -> tuple[int, int]:
        """
        The limit expressed as a 2-tuple of the maximum and the period (in seconds).
        """
        return self._limit

    def match(self, request: ClientRequest, /) -> bool:
        """
        Check the rate limit matches the given URL.
        """
        url = str(request.url)
        if isinstance(self._match, str):
            return url.startswith(self._match)
        return self._match.fullmatch(url) is not None
