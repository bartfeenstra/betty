"""Define Betty's core application functionality."""

from __future__ import annotations

from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import asynccontextmanager
from multiprocessing import get_context
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Self, Any, final, TypeVar, cast

import aiohttp
from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

from betty import fs
from betty.app import config
from betty.app.config import AppConfiguration
from betty.app.factory import AppDependentFactory
from betty.assets import AssetRepository
from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.cache.no_op import NoOpCache
from betty.config import Configurable, assert_configuration_file
from betty.core import CoreComponent
from betty.factory import new, FactoryProvider
from betty.fetch import Fetcher, http
from betty.fetch.static import StaticFetcher
from betty.fs import HOME_DIRECTORY_PATH
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import Localizer, LocalizerRepository

if TYPE_CHECKING:
    from betty.cache import Cache
    from collections.abc import AsyncIterator, Callable, Awaitable

_T = TypeVar("_T")


@final
class App(Configurable[AppConfiguration], FactoryProvider[Any], CoreComponent):
    """
    The Betty application.
    """

    def __init__(
        self,
        configuration: AppConfiguration,
        cache_directory_path: Path,
        *,
        cache_factory: Callable[[Self], Cache[Any]],
        fetcher: Fetcher | None = None,
    ):
        super().__init__()
        self._configuration = configuration
        self._assets: AssetRepository | None = None
        self._localization_initialized = False
        self._localizer: Localizer | None = None
        self._localizers: LocalizerRepository | None = None
        self._http_client: aiohttp.ClientSession | None = None
        self._fetcher = fetcher
        self._cache_directory_path = cache_directory_path
        self._cache: Cache[Any] | None = None
        self._cache_factory = cache_factory
        self._binary_file_cache: BinaryFileCache | None = None
        self._process_pool: Executor | None = None

    @classmethod
    @asynccontextmanager
    async def new_from_environment(cls) -> AsyncIterator[Self]:
        """
        Create a new application from the environment.
        """
        configuration = AppConfiguration()
        if config.CONFIGURATION_FILE_PATH.exists():
            assert_configuration_file(configuration)(config.CONFIGURATION_FILE_PATH)
        yield cls(
            configuration,
            Path(environ.get("BETTY_CACHE_DIRECTORY", HOME_DIRECTORY_PATH / "cache")),
            cache_factory=lambda app: PickledFileCache[Any](app._cache_directory_path),
        )

    @classmethod
    @asynccontextmanager
    async def new_temporary(
        cls, *, fetcher: Fetcher | None = None
    ) -> AsyncIterator[Self]:
        """
        Creat a new, temporary, isolated application.

        The application will not use any persistent caches, or leave
        any traces on the system.
        """
        async with (
            TemporaryDirectory() as cache_directory_path_str,
        ):
            yield cls(
                AppConfiguration(),
                Path(cache_directory_path_str),
                cache_factory=lambda app: NoOpCache(),
                fetcher=fetcher or StaticFetcher(),
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
    def localizer(self) -> Awaitable[Localizer]:
        """
        Get the application's localizer.
        """
        return self._get_localizer()

    async def _get_localizer(self) -> Localizer:
        if self._localizer is None:
            self._assert_bootstrapped()
            self._localizer = await self.localizers.get_negotiated(
                self.configuration.locale or DEFAULT_LOCALE
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
    def http_client(self) -> Awaitable[aiohttp.ClientSession]:
        """
        The HTTP client.
        """
        return self._get_http_client()

    async def _get_http_client(self) -> aiohttp.ClientSession:
        if self._http_client is None:
            self._assert_bootstrapped()
            self._http_client = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit_per_host=5),
                headers={
                    "User-Agent": "Betty (https://betty.readthedocs.io/)",
                },
            )
            await self._async_exit_stack.enter_async_context(self._http_client)
        return self._http_client

    @property
    def fetcher(self) -> Awaitable[Fetcher]:
        """
        The fetcher.
        """
        return self._get_fetcher()

    async def _get_fetcher(self) -> Fetcher:
        if self._fetcher is None:
            self._assert_bootstrapped()
            self._fetcher = http.HttpFetcher(
                await self.http_client,
                self.cache.with_scope("fetch"),
                self.binary_file_cache.with_scope("fetch"),
            )
        return self._fetcher

    @property
    def cache(self) -> Cache[Any]:
        """
        The cache.
        """
        if self._cache is None:
            self._assert_bootstrapped()
            self._cache = self._cache_factory(self)
        return self._cache

    @property
    def binary_file_cache(self) -> BinaryFileCache:
        """
        The binary file cache.
        """
        if self._binary_file_cache is None:
            self._assert_bootstrapped()
            self._binary_file_cache = BinaryFileCache(self._cache_directory_path)
        return self._binary_file_cache

    @property
    def process_pool(self) -> Executor:
        """
        The shared process pool.

        Use this to run CPU/computationally-heavy tasks in other processes.
        """
        if self._process_pool is None:
            self._assert_bootstrapped()
            # Avoid `fork` so as not to start worker processes with unneeded resources.
            # Settle for `spawn` so all environments use the same start method.
            self._process_pool = ProcessPoolExecutor(mp_context=get_context("spawn"))
        return self._process_pool

    @override
    async def new(self, cls: type[_T]) -> _T:
        """
        Create a new instance.

        :return:
            #. If ``cls`` extends :py:class:`betty.app.factory.AppDependentFactory`, this will call return ``cls``'s
                ``new()``'s return value.
            #. If ``cls`` extends :py:class:`betty.factory.IndependentFactory`, this will call return ``cls``'s
                ``new()``'s return value.
            #. Otherwise ``cls()`` will be called without arguments, and the resulting instance will be returned.

        :raises FactoryError: raised when ``cls`` could not be instantiated.
        """
        if issubclass(cls, AppDependentFactory):
            return cast(_T, await cls.new_for_app(self))
        return await new(cls)
