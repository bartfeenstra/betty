"""Define Betty's core application functionality."""

from __future__ import annotations

import multiprocessing
from contextlib import asynccontextmanager
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast, final

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
from betty.factory import TargetFactory, new
from betty.fetch import Fetcher, http
from betty.fetch.static import StaticFetcher
from betty.fs import HOME_DIRECTORY_PATH
from betty.license import LICENSE_REPOSITORY, License
from betty.license.licenses import SpdxLicenseRepository
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import Localizer, LocalizerRepository
from betty.multiprocessing import ProcessPoolExecutor
from betty.plugin.proxy import ProxyPluginRepository
from betty.service import ServiceFactory, ServiceProvider, StaticService, service
from betty.typing import processsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from concurrent import futures
    from multiprocessing.managers import SyncManager

    from betty.cache import Cache
    from betty.plugin import PluginRepository

_T = TypeVar("_T")


@final
@processsafe
class App(Configurable[AppConfiguration], TargetFactory, ServiceProvider):
    """
    The Betty application.
    """

    def __init__(
        self,
        configuration: AppConfiguration,
        cache_directory_path: Path,
        *,
        cache_factory: ServiceFactory[Self, Cache[Any]],
        fetcher: Fetcher | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
        multiprocessing_manager: SyncManager | None = None,
    ):
        cls = type(self)
        super().__init__(configuration=configuration)
        if fetcher is not None:
            cls.fetcher.override(self, fetcher)
        if process_pool is not None:
            cls.process_pool.override(self, process_pool)
        if multiprocessing_manager is not None:
            cls.multiprocessing_manager.override(self, multiprocessing_manager)
        self._cache_directory_path = cache_directory_path
        cls.cache.override_factory(self, cache_factory)

    def __getstate__(self) -> dict[str, Any]:
        cls = type(self)
        return {
            **super().__getstate__(),
            "_bootstrapped": True,
            "_cache_directory_path": self._cache_directory_path,
            "_configuration": self._configuration,
            **cls.binary_file_cache.get_state(self),
            **cls.cache.get_state(self),
        }

    @classmethod
    @asynccontextmanager
    async def new_from_environment(cls) -> AsyncIterator[Self]:
        """
        Create a new application from the environment.
        """
        configuration = AppConfiguration()
        if config.CONFIGURATION_FILE_PATH.exists():
            (await assert_configuration_file(configuration))(
                config.CONFIGURATION_FILE_PATH
            )
        yield cls(
            configuration,
            Path(environ.get("BETTY_CACHE_DIRECTORY", HOME_DIRECTORY_PATH / "cache")),
            cache_factory=lambda app: PickledFileCache[Any](
                app._cache_directory_path, manager=app.multiprocessing_manager
            ),
        )

    @classmethod
    @asynccontextmanager
    async def new_temporary(
        cls,
        *,
        cache_factory: ServiceFactory[Self, Cache[Any]] | None = None,
        fetcher: Fetcher | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
        multiprocessing_manager: SyncManager | None = None,
    ) -> AsyncIterator[Self]:
        """
        Create a new, temporary, isolated application.

        The application will not use any persistent caches, or leave
        any traces on the system.
        """
        async with (
            TemporaryDirectory() as cache_directory_path_str,
        ):
            yield cls(
                AppConfiguration(),
                Path(cache_directory_path_str),
                cache_factory=cache_factory or StaticService(NoOpCache()),
                fetcher=fetcher or StaticFetcher(),
                process_pool=process_pool,
                multiprocessing_manager=multiprocessing_manager,
            )

    @service
    def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        return AssetRepository(fs.ASSETS_DIRECTORY_PATH)

    @service
    async def localizer(self) -> Localizer:
        """
        Get the application's localizer.
        """
        return await self.localizers.get_negotiated(
            self.configuration.locale or DEFAULT_LOCALE
        )

    @service
    def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        return LocalizerRepository(self.assets)

    @service
    async def http_client(self) -> aiohttp.ClientSession:
        """
        The HTTP client.
        """
        http_client = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit_per_host=5),
            headers={
                "User-Agent": "Betty (https://betty.readthedocs.io/)",
            },
        )

        async def _shutdown(wait: bool) -> None:
            await http_client.close()

        self._shutdown_stack.append(_shutdown)
        return http_client

    @service
    async def fetcher(self) -> Fetcher:
        """
        The fetcher.
        """
        return http.HttpFetcher(
            await self.http_client,
            self.cache.with_scope("fetch"),
            self.binary_file_cache.with_scope("fetch"),
        )

    @service(shared=True)
    def cache(self) -> Cache[Any]:
        """
        The cache.
        """
        raise NotImplementedError

    @service(shared=True)
    def binary_file_cache(self) -> BinaryFileCache:
        """
        The binary file cache.
        """
        return BinaryFileCache(
            self._cache_directory_path, manager=self.multiprocessing_manager
        )

    @service
    def process_pool(self) -> futures.ProcessPoolExecutor:
        """
        The shared process pool.

        Use this to run CPU/computationally-heavy tasks in other processes.
        """
        process_pool = ProcessPoolExecutor()

        async def _shutdown(wait: bool) -> None:
            process_pool.shutdown(wait, cancel_futures=not wait)

        self._shutdown_stack.append(_shutdown)
        return process_pool

    @service
    def multiprocessing_manager(self) -> SyncManager:
        """
        The multiprocessing manager.

        Use this to create process-safe synchronization primitives.
        """
        manager = multiprocessing.Manager()

        async def _shutdown(wait: bool) -> None:
            manager.shutdown(wait)

        self._shutdown_stack.append(_shutdown)
        return manager

    @override
    async def new_target(self, cls: type[_T]) -> _T:
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

    @service
    async def spdx_license_repository(self) -> PluginRepository[License]:
        """
        The SPDX licenses available to this application.
        """
        return ProxyPluginRepository(
            LICENSE_REPOSITORY,
            SpdxLicenseRepository(
                binary_file_cache=self.binary_file_cache.with_scope("spdx"),
                fetcher=await self.fetcher,
                localizer=await self.localizer,
                factory=self.new_target,
                process_pool=self.process_pool,
                manager=self.multiprocessing_manager,
            ),
        )
