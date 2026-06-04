import time
from asyncio import gather
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from typing import Final
from unittest.mock import AsyncMock

import pytest
from aiohttp.client_reqrep import ClientRequest, ClientResponse
from yarl import URL

from betty.http_client.rate_limit import RateLimitDefinition, RateLimitMiddleware

_low_rate_limit: Final[RateLimitDefinition] = RateLimitDefinition(
    "-", limit=(1, 999999999), match=""
)
_high_rate_limit: Final[RateLimitDefinition] = RateLimitDefinition(
    "-", limit=(999999999, 1), match=""
)
_never_rate_limit: Final[RateLimitDefinition] = RateLimitDefinition(
    "-", limit=(1, 999999999), match="x" * 999999999
)


type DoAssert = Callable[[int, int, Sequence[RateLimitDefinition]], Awaitable[None]]


class TestRateLimitMiddleware:
    @pytest.fixture
    async def do_assert(self) -> AsyncIterator[DoAssert]:
        m_response = AsyncMock(spec=ClientResponse)
        handler_called_request = []

        async def _handler(request: ClientRequest) -> ClientResponse:
            handler_called_request.append(request)
            return m_response

        request = ClientRequest("GET", URL("https://example.com"))

        async def _do_assert(
            expected: int, consumers: int, limits: Sequence[RateLimitDefinition]
        ) -> None:
            sut = RateLimitMiddleware(limits)

            async def _task() -> None:
                assert await sut(request, _handler) is m_response

            start = time.time()
            await gather(*(_task() for _ in range(consumers)))
            end = time.time()
            duration = end - start
            assert duration >= expected

        yield _do_assert

        assert handler_called_request[0] is request

    async def test___call___without_limits(self) -> None:
        m_response = AsyncMock(spec=ClientResponse)
        handler_called_request = []

        async def _handler(request: ClientRequest) -> ClientResponse:
            handler_called_request.append(request)
            return m_response

        request = ClientRequest("GET", URL("https://example.com"))
        sut = RateLimitMiddleware(())
        assert await sut(request, _handler) is m_response
        assert handler_called_request[0] is request

    @pytest.mark.parametrize(
        ("expected", "consumers"),
        [
            (0, 1),
            (1, 100),
        ],
    )
    async def test___call____with_limits_without_match(
        self, expected: int, consumers: int, do_assert: DoAssert
    ) -> None:
        await do_assert(
            expected,
            consumers,
            [_never_rate_limit, _never_rate_limit, _never_rate_limit],
        )

    @pytest.mark.parametrize(
        ("expected", "consumers"),
        [
            (0, 1),
            (0, 100),
        ],
    )
    async def test___call____with_limits_with_match(
        self, expected: int, consumers: int, do_assert: DoAssert
    ) -> None:
        await do_assert(
            expected,
            consumers,
            [_never_rate_limit, _high_rate_limit, _low_rate_limit],
        )
