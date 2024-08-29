"""Define Betty's core application functionality."""

from __future__ import annotations

from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import asynccontextmanager
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Self, Any, final

import aiohttp
from aiofiles.tempfile import TemporaryDirectory

from betty import fs
from betty.app import config
from betty.app.config import AppConfiguration
from betty.assets import AssetRepository
from betty.asyncio import wait_to_thread
from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.cache.memory import MemoryCache
from betty.cache.no_op import NoOpCache
from betty.config import Configurable, assert_configuration_file
from betty.core import CoreComponent
from betty.fetch import Fetcher, http
from betty.fs import HOME_DIRECTORY_PATH
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import Localizer, LocalizerRepository

if TYPE_CHECKING:
    from betty.serde.dump import Dump
    from betty.cache import Cache
    from collections.abc import AsyncIterator, Callable


@final
class App(Configurable[AppConfiguration], CoreComponent):
    """
    The Betty application.
    """

    def __init__(
        self,
        *,
        configuration: AppConfiguration,
        cache: Cache[Any],
        binary_file_cache: BinaryFileCache,
    ):
        super().__init__()
        self._configuration = configuration
        self._assets: AssetRepository | None = None
        self._localization_initialized = False
        self._localizer: Localizer | None = None
        self._localizers: LocalizerRepository | None = None
        self._http_client: aiohttp.ClientSession | None = None
        self._fetcher: Fetcher | None = None
        self._cache = cache
        self._binary_file_cache = binary_file_cache
        self._process_pool: Executor | None = None

    def __reduce__(
        self,
    ) -> tuple[
        Callable[[Dump, Path, Cache[Any], BinaryFileCache], Self],
        tuple[Dump, Path, Cache[Any], BinaryFileCache],
    ]:
        return self._unreduce, (  # type: ignore[return-value]
            self.configuration.dump(),
            self._cache,
            self._binary_file_cache,
        )

    # @todo
    @staticmethod
    def _unreduce_cache_factory(app: App) -> Cache[Any]:
        return MemoryCache()

    @classmethod
    def _unreduce(
        cls,
        configuration_dump: Dump,
        cache: Cache[Any],
        binary_file_cache: BinaryFileCache,
        /,
    ) -> Self:
        configuration = AppConfiguration()
        configuration.load(configuration_dump)
        return cls(
            configuration=configuration,
            cache=cache,
            binary_file_cache=binary_file_cache,
        )

    @classmethod
    @asynccontextmanager
    async def new_from_environment(cls) -> AsyncIterator[Self]:
        """
        Create a new application from the environment.
        """
        configuration = AppConfiguration()
        if config.CONFIGURATION_FILE_PATH.exists():
            assert_configuration_file(configuration)(config.CONFIGURATION_FILE_PATH)
        cache_directory_path = Path(
            environ.get("BETTY_CACHE_DIRECTORY", HOME_DIRECTORY_PATH / "cache")
        )
        yield cls(
            configuration=configuration,
            cache=PickledFileCache[Any](cache_directory_path),
            binary_file_cache=BinaryFileCache(cache_directory_path),
        )

    @classmethod
    @asynccontextmanager
    async def new_temporary(cls) -> AsyncIterator[Self]:
        """
        Creat a new, temporary, isolated application.

        The application will not use any persistent caches, or leave
        any traces on the system.
        """
        async with (
            TemporaryDirectory() as cache_directory_path_str,
        ):
            yield cls(
                configuration=AppConfiguration(),
                cache=NoOpCache(),
                binary_file_cache=BinaryFileCache(Path(cache_directory_path_str)),
            )

    @property
    def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        if self._assets is None:
            self._assert_bootstrapped()
            self._assets = AssetRepository(fs.ASSETS_DIRECTORY_PATH)
        return self._assets

    @property
    def localizer(self) -> Localizer:
        """
        Get the application's localizer.
        """
        if self._localizer is None:
            self._assert_bootstrapped()
            self._localizer = wait_to_thread(
                self.localizers.get_negotiated(
                    self.configuration.locale or DEFAULT_LOCALE
                )
            )
        return self._localizer

    @property
    def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        if self._localizers is None:
            self._assert_bootstrapped()
            self._localizers = LocalizerRepository(self.assets)
        return self._localizers

    @property
    def http_client(self) -> aiohttp.ClientSession:
        """
        The HTTP client.
        """
        if self._http_client is None:
            self._assert_bootstrapped()
            self._http_client = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit_per_host=5),
                headers={
                    "User-Agent": "Betty (https://github.com/bartfeenstra/betty)",
                },
            )
            wait_to_thread(
                self._async_exit_stack.enter_async_context(self._http_client)
            )
        return self._http_client

    @property
    def fetcher(self) -> Fetcher:
        """
        The fetcher.
        """
        if self._fetcher is None:
            self._assert_bootstrapped()
            self._fetcher = http.HttpFetcher(
                self.http_client,
                self.cache.with_scope("fetch"),
                self.binary_file_cache.with_scope("fetch"),
            )
        return self._fetcher

    @property
    def cache(self) -> Cache[Any]:
        """
        The cache.
        """
        return self._cache

    @property
    def binary_file_cache(self) -> BinaryFileCache:
        """
        The binary file cache.
        """
        return self._binary_file_cache

    @property
    def process_pool(self) -> Executor:
        """
        The shared process pool.

        Use this to run CPU/computationally-heavy tasks in other processes.
        """
        if self._process_pool is None:
            self._assert_bootstrapped()
            self._process_pool = ProcessPoolExecutor()
        return self._process_pool
