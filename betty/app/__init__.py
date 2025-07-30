"""Define Betty's core application functionality."""

from __future__ import annotations

from contextlib import asynccontextmanager
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast, final

import aiohttp
from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

import betty
from betty.app import config
from betty.app.config import AppConfiguration
from betty.app.factory import AppDependentFactory
from betty.asset import AssetRepository, StaticAssetRepository
from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.cache.no_op import NoOpCache
from betty.config import Configurable
from betty.config.file import assert_configuration_file
from betty.dirs import CACHE_DIRECTORY_PATH
from betty.factory import TargetFactory, new
from betty.fetch import Fetcher, http
from betty.fetch.static import StaticFetcher
from betty.license import LICENSE_REPOSITORY, License
from betty.license.licenses import SpdxLicenseRepository
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import Localizer, LocalizerRepository
from betty.locale.translation import (
    AssetTranslationRepository,
    NoOpTranslationRepository,
    TranslationRepository,
)
from betty.multiprocessing import ProcessPoolExecutor
from betty.plugin.proxy import ProxyPluginRepository
from betty.service import ServiceFactory, ServiceProvider, StaticService, service
from betty.typing import processsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from concurrent import futures

    from betty.cache import Cache
    from betty.plugin import PluginRepository
    from betty.user import User

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
        user: User | None = None,
        cache_factory: ServiceFactory[Self, Cache[Any]],
        fetcher: Fetcher | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
        translations: TranslationRepository | None = None,
    ):
        from betty.console.user import ConsoleUser

        cls = type(self)
        super().__init__(configuration=configuration)
        self._user = user or ConsoleUser()
        if fetcher is not None:
            cls.fetcher.override(self, fetcher)
        if process_pool is not None:
            cls.process_pool.override(self, process_pool)
        if translations is not None:
            cls.translations.override(self, translations)
        self._cache_directory_path = cache_directory_path
        cls.cache.override_factory(self, cache_factory)

    @override
    def __getstate__(self) -> dict[str, Any]:
        return {
            **super().__getstate__(),
            "_cache_directory_path": self._cache_directory_path,
            "_configuration": self._configuration,
            "_user": self._user,
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
            Path(environ.get("BETTY_CACHE_DIRECTORY", CACHE_DIRECTORY_PATH)),
            cache_factory=lambda app: PickledFileCache[Any](app._cache_directory_path),
        )

    @classmethod
    @asynccontextmanager
    async def new_temporary(
        cls,
        *,
        cache_factory: ServiceFactory[Self, Cache[Any]] | None = None,
        fetcher: Fetcher | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
        user: User | None = None,
        translations: TranslationRepository | None | False = False,
    ) -> AsyncIterator[Self]:
        """
        Create a new, temporary, isolated application.

        The application will not use any persistent caches, or leave
        any traces on the system.
        """
        async with (
            TemporaryDirectory() as cache_directory_path_str,
        ):
            cache_directory_path = Path(cache_directory_path_str)
            yield cls(
                AppConfiguration(),
                cache_directory_path,
                cache_factory=cache_factory or StaticService(NoOpCache()),
                fetcher=fetcher or StaticFetcher(),
                process_pool=process_pool,
                user=user,
                translations=NoOpTranslationRepository()
                if translations is False
                else translations,
            )

    @override
    async def bootstrap(self) -> None:
        await super().bootstrap()
        await self._user.connect()
        self._user.localizer = await self.localizer

    @override
    async def shutdown(self, *, wait: bool = True) -> None:
        await self._user.disconnect()
        await super().shutdown(wait=wait)

    @property
    def user(self) -> User:
        """
        The current user session.
        """
        return self._user

    @service
    def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        return StaticAssetRepository(betty.ASSETS_DIRECTORY_PATH)

    @service
    async def translations(self) -> TranslationRepository:
        """
        The available translations.
        """
        translations = AssetTranslationRepository(self.assets, self.binary_file_cache)
        await translations.bootstrap()
        return translations

    @service
    async def localizer(self) -> Localizer:
        """
        Get the application's user-facing localizer.
        """
        return (await self.localizers).get(self.configuration.locale or DEFAULT_LOCALE)

    @service
    async def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        return LocalizerRepository(await self.translations)

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
            user=self.user,
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
        return BinaryFileCache(self._cache_directory_path)

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
            License,
            LICENSE_REPOSITORY,
            SpdxLicenseRepository(
                binary_file_cache=self.binary_file_cache.with_scope("spdx"),
                fetcher=await self.fetcher,
                user=self.user,
                factory=self.new_target,
                process_pool=self.process_pool,
            ),
        )
