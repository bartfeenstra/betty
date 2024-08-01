"""
Fetch content from the internet.
"""

import asyncio
from collections.abc import Callable, Awaitable
from logging import getLogger
from pathlib import Path
from time import time
from typing import TypeVar

from aiohttp import ClientSession, ClientResponse, ClientError
from betty.cache import Cache
from betty.cache.file import BinaryFileCache
from betty.fetch import Fetcher, FetchResponse, FetchError
from betty.hashid import hashid
from betty.locale.localizable import plain
from typing_extensions import override

_CacheItemValueT = TypeVar("_CacheItemValueT")


class HttpFetcher(Fetcher):
    """
    Fetch content from the internet using an HTTP client.
    """

    def __init__(
        self,
        http_client: ClientSession,
        response_cache: Cache[FetchResponse],
        binary_file_cache: BinaryFileCache,
        # Default to seven days.
        ttl: int = 86400 * 7,
    ):
        self._response_cache = response_cache
        self._binary_file_cache = binary_file_cache
        self._ttl = ttl
        self._http_client = http_client
        self._logger = getLogger(__name__)

    async def _fetch(
        self,
        url: str,
        cache: Cache[_CacheItemValueT],
        response_mapper: Callable[[ClientResponse], Awaitable[_CacheItemValueT]],
    ) -> tuple[_CacheItemValueT, str]:
        cache_item_id = hashid(url)

        response_data: _CacheItemValueT | None = None
        async with cache.getset(cache_item_id) as (cache_item, setter):
            if cache_item and cache_item.modified + self._ttl > time():
                response_data = await cache_item.value()
            else:
                self._logger.debug(f'Fetching "{url}"...')
                try:
                    async with self._http_client.get(url) as response:
                        response_data = await response_mapper(response)
                except ClientError as error:
                    self._logger.warning(
                        f'Could not successfully connect to "{url}": {error}'
                    )
                except asyncio.TimeoutError:
                    self._logger.warning(f'Timeout when connecting to "{url}"')
                else:
                    await setter(response_data)

        if response_data is None:
            if cache_item:
                response_data = await cache_item.value()
            else:
                raise FetchError(
                    plain(
                        f'Could neither fetch "{url}", nor find an old version in the cache.'
                    )
                )

        return response_data, cache_item_id

    async def _map_response(self, response: ClientResponse) -> FetchResponse:
        return FetchResponse(
            response.headers.copy(),
            await response.read(),
            response.get_encoding(),
        )

    @override
    async def fetch(self, url: str) -> FetchResponse:
        """
        Fetch an HTTP resource.
        """
        response_data, _ = await self._fetch(
            url, self._response_cache, self._map_response
        )
        return response_data

    @override
    async def fetch_file(self, url: str) -> Path:
        """
        Fetch a file.

        :return: The path to the file on disk.
        """
        _, cache_item_id = await self._fetch(
            url, self._binary_file_cache, ClientResponse.read
        )
        return self._binary_file_cache.cache_item_file_path(cache_item_id)
