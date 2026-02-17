import time
from asyncio import gather
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from typing import override
from unittest.mock import AsyncMock

import pytest
from aiohttp.client_reqrep import ClientRequest, ClientResponse
from yarl import URL

from betty.http_client.rate_limit import (
    RateLimit,
    RateLimitMiddleware,
)


class _LowRateLimit(RateLimit):
    @override
    @property
    def limit(self) -> tuple[int, int]:
        return 1, 999999999


class _NeverMatchingRateLimit(_LowRateLimit):
    @override
    def match(self, request: ClientRequest) -> bool:
        return False


class _AlwaysMatchingLowRateLimit(_LowRateLimit):
    @override
    def match(self, request: ClientRequest) -> bool:
        return True


class _AlwaysMatchingHighRateLimit(RateLimit):
    @override
    def match(self, request: ClientRequest) -> bool:
        return True

    @override
    @property
    def limit(self) -> tuple[int, int]:
        return 999999999, 1


type DoAssert = Callable[[int, int, Sequence[RateLimit]], Awaitable[None]]


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
            expected: int, consumers: int, limits: Sequence[RateLimit]
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
            [
                _NeverMatchingRateLimit(),
                _NeverMatchingRateLimit(),
                _NeverMatchingRateLimit(),
            ],
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
            [
                _NeverMatchingRateLimit(),
                _AlwaysMatchingHighRateLimit(),
                _AlwaysMatchingLowRateLimit(),
            ],
        )
