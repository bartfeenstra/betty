import asyncio
from typing import AsyncIterator

import aiofiles
import pytest
from aiohttp import ClientSession, ClientError
from aioresponses import aioresponses

from betty.cache.file import BinaryFileCache
from betty.cache.memory import MemoryCache
from betty.fetch import FetchError
from betty.fetch.http import HttpFetcher


class TestHttpFetcher:
    @pytest.fixture()
    async def sut(
        self, binary_file_cache: BinaryFileCache
    ) -> AsyncIterator[HttpFetcher]:
        async with ClientSession() as http_client:
            yield HttpFetcher(http_client, MemoryCache(), binary_file_cache)

    async def test_fetch_should_return(
        self, aioresponses: aioresponses, sut: HttpFetcher
    ) -> None:
        url = "https://example.com"
        content = "The name's Text. Plain Text."
        aioresponses.get(url, body=content, headers={"X-Betty": content})

        # The first fetch uses cold caches. This should result in the HTTP client being called.
        fetched_once = await sut.fetch(url)
        assert fetched_once.text == content
        assert fetched_once.headers["X-Betty"] == content

        # The second fetch should result in the cache being called.
        fetched_twice = await sut.fetch(url)
        assert fetched_twice.text == content
        assert fetched_twice.headers["X-Betty"] == content

        # Assert the HTTP client was indeed called only once.
        aioresponses.assert_called_once()

    @pytest.mark.parametrize(
        "error",
        [
            ClientError(),
            asyncio.TimeoutError(),
        ],
    )
    async def test_fetch_with_cold_cache_and_get_error_should_error(
        self, aioresponses: aioresponses, error: Exception, sut: HttpFetcher
    ) -> None:
        url = "https://example.com"
        aioresponses.get(url, exception=error)

        with pytest.raises(FetchError):
            await sut.fetch(url)

    @pytest.mark.parametrize(
        "error",
        [
            ClientError(),
            asyncio.TimeoutError(),
        ],
    )
    async def test_fetch_with_warm_cache_and_get_error_should_return(
        self,
        aioresponses: aioresponses,
        binary_file_cache: BinaryFileCache,
        error: Exception,
        sut: HttpFetcher,
    ) -> None:
        async with ClientSession() as http_client:
            sut = HttpFetcher(
                http_client,
                MemoryCache(),
                binary_file_cache,
                # A negative TTL ensures every cache item is considered expired a long time ago.
                -999999999,
            )
            url = "https://example.com"
            content = "The name's Text. Plain Text."
            aioresponses.get(url, body=content, headers={"X-Betty": content})

            # The first fetch uses cold caches. This should result in the HTTP client being called.
            fetched_once = await sut.fetch(url)
            assert fetched_once.text == content
            assert fetched_once.headers["X-Betty"] == content

            aioresponses.get(url, exception=error)

            # The second fetch should result in:
            # - the cache being called, but the item being ignored due to our negative TTL
            # - the call to the HTTP client raising an error
            # - the expired cached content being returned
            fetched_twice = await sut.fetch(url)
            assert fetched_twice.text == content
            assert fetched_twice.headers["X-Betty"] == content

    async def test_fetch_file_should_return(
        self, aioresponses: aioresponses, sut: HttpFetcher
    ) -> None:
        url = "https://example.com"
        content = b"The name's Text. Plain Text."
        aioresponses.get(url, body=content)

        # The first fetch uses cold caches. This should result in the HTTP client being called.
        fetched_once = await sut.fetch_file(url)
        async with aiofiles.open(fetched_once, "rb") as f:
            assert await f.read() == content

        # The second fetch should result in the cache being called.
        fetched_twice = await sut.fetch_file(url)
        async with aiofiles.open(fetched_twice, "rb") as f:
            assert await f.read() == content

        # Assert the HTTP client was indeed called only once.
        aioresponses.assert_called_once()

    @pytest.mark.parametrize(
        "error",
        [
            ClientError(),
            asyncio.TimeoutError(),
        ],
    )
    async def test_fetch_file_with_cold_cache_and_get_error_should_error(
        self, aioresponses: aioresponses, error: Exception, sut: HttpFetcher
    ) -> None:
        url = "https://example.com"
        aioresponses.get(url, exception=error)

        with pytest.raises(FetchError):
            await sut.fetch_file(url)

    @pytest.mark.parametrize(
        "error",
        [
            ClientError(),
            asyncio.TimeoutError(),
        ],
    )
    async def test_fetch_file_with_warm_cache_and_get_error_should_return(
        self,
        aioresponses: aioresponses,
        binary_file_cache: BinaryFileCache,
        error: Exception,
        sut: HttpFetcher,
    ) -> None:
        async with ClientSession() as http_client:
            sut = HttpFetcher(
                http_client,
                MemoryCache(),
                binary_file_cache,
                # A negative TTL ensures every cache item is considered expired a long time ago.
                -999999999,
            )
            url = "https://example.com"
            content = b"The name's Text. Plain Text."
            aioresponses.get(url, body=content)

            # The first fetch uses cold caches. This should result in the HTTP client being called.
            fetched_once = await sut.fetch_file(url)
            async with aiofiles.open(fetched_once, "rb") as f:
                assert await f.read() == content

            aioresponses.get(url, exception=error)

            # The second fetch should result in:
            # - the cache being called, but the item being ignored due to our negative TTL
            # - the call to the HTTP client raising an error
            # - the expired cached content being returned
            fetched_twice = await sut.fetch_file(url)
            async with aiofiles.open(fetched_twice, "rb") as f:
                assert await f.read() == content
