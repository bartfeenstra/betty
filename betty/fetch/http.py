"""
Fetch content from the internet.
"""

from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from logging import getLogger
from pathlib import Path
from time import time
from typing import TypeVar
from urllib.parse import urlparse

from aiohttp import ClientError, ClientResponse, ClientSession
from typing_extensions import override

from betty.cache import Cache, CacheItem, CacheItemValueSetter
from betty.cache.file import BinaryFileCache
from betty.fetch import Fetcher, FetchError, FetchResponse
from betty.locale.localizable import plain

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
        getsetter: Callable[
            [],
            AbstractAsyncContextManager[
                tuple[
                    CacheItem[_CacheItemValueT] | None,
                    CacheItemValueSetter[_CacheItemValueT],
                ]
            ],
        ],
        response_mapper: Callable[[ClientResponse], Awaitable[_CacheItemValueT]],
    ) -> _CacheItemValueT:
        response_data: _CacheItemValueT | None = None
        async with getsetter() as (cache_item, setter):
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
                except TimeoutError:
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

        return response_data

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
        return await self._fetch(
            url, lambda: self._response_cache.getset(url), self._map_response
        )

    @override
    async def fetch_file(self, url: str) -> Path:
        """
        Fetch a file.

        :return: The path to the file on disk.
        """
        suffix = Path(urlparse(url).path).suffix or None
        if suffix:
            suffix = suffix.lower()
        await self._fetch(
            url,
            lambda: self._binary_file_cache.getset(url, suffix=suffix),
            ClientResponse.read,
        )
        return self._binary_file_cache.cache_item_file_path(url, suffix)
