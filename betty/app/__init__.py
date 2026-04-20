"""Define Betty's core application functionality."""

from __future__ import annotations

from asyncio import to_thread
from concurrent import futures
from contextlib import AsyncExitStack, asynccontextmanager
from os import environ
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any, Literal, Self, final, override

from aiohttp_client_cache.backends.filesystem import FileBackend
from aiohttp_client_cache.session import CachedSession

from betty.app.data import AppConfiguration
from betty.asset import AssetDefinition, AssetRepositoryService
from betty.cache import Cache
from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.cache.no_op import NoOpCache
from betty.dirs import CACHE_DIRECTORY
from betty.factory import DataManufacturable
from betty.http_client import ClientErrorToUserMessageMiddleware
from betty.http_client.rate_limit import RateLimitDefinition, RateLimitMiddleware
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.locale import DEFAULT_LOCALE, ResolvableLocale, resolve_locale
from betty.locale.localize import Localizer, LocalizerRepository
from betty.locale.translation import (
    DEFAULT_TRANSLATION_REPOSITORY,
    AssetTranslationRepository,
    TranslationRepository,
)
from betty.multiprocessing import ProcessPoolExecutor
from betty.portable.file import assert_load_file
from betty.service import Service
from betty.service.plugin import PluginServiceProvider, SupportedPlugins
from betty.service.plugin.definition.collection.keyed import (
    PluginDefinitionsService,
)
from betty.service.simple import service
from betty.service_level import DownstreamServiceLevel, Plugins, ServiceLevel
from betty.service_level.requirement import RequirableServiceLevel
from betty.typing import threadsafe
from betty.universe import UNIVERSE
from betty.user.no_op import NoOpUser

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable, Mapping

    import aiohttp

    from betty.plugin import PluginDefinition
    from betty.plugin.discovery import ResolvableDiscovery
    from betty.plugin.resolve import ResolvablePluginDefinition
    from betty.service.simple.asynchronous import TypedAsynchronousServiceOrFactory
    from betty.service.simple.synchronous import TypedSynchronousServiceOrFactory
    from betty.user import User


@final
@threadsafe
class App(
    DataManufacturable[AppConfiguration],
    DownstreamServiceLevel,
    RequirableServiceLevel,
    PluginServiceProvider,
):
    """
    The Betty application.

    .. list-table::
       :widths: 20 10
       :header-rows: 0

       * - Configuration
         - :py:class:`betty.app.data.AppConfiguration`
    """

    assets = AssetRepositoryService()
    rate_limits = PluginDefinitionsService(RateLimitDefinition)

    def __init__(
        self,
        *,
        assets: Iterable[ResolvablePluginDefinition[AssetDefinition]] = (),
        cache_directory: Path | None = None,
        cache: TypedSynchronousServiceOrFactory[App, Cache[Any]] | None = None,
        locale: ResolvableLocale | None = None,
        plugins: Plugins | None = None,
        process_pool: TypedSynchronousServiceOrFactory[App, futures.ProcessPoolExecutor]
        | None = None,
        rate_limits: Iterable[RateLimitDefinition] = (),
        supported_plugins: SupportedPlugins = (),
        translations: TypedAsynchronousServiceOrFactory[App, TranslationRepository]
        | None = None,
        user: User | None = None,
    ):
        from betty.rich.user import RichUser

        cls = type(self)
        if process_pool is not None:
            cls.process_pool.override(
                self,
                Service(process_pool)
                if isinstance(process_pool, futures.ProcessPoolExecutor)
                else process_pool,
            )
        if translations is not None:
            cls.translations.override(
                self,
                Service(translations)
                if isinstance(translations, TranslationRepository)
                else translations,
            )
        if cache is not None:
            cls.cache.override(
                self, Service(cache) if isinstance(cache, Cache) else cache
            )
        super().__init__(
            plugins=plugins, supported_plugins=supported_plugins, upstream=UNIVERSE
        )
        cls.assets.add_init_plugins(self, *assets)
        cls.rate_limits.add_init_plugins(self, *rate_limits)
        self.life_cycle.on_bootstrap(self._bootstrap_localizer)
        self._locale = DEFAULT_LOCALE if locale is None else resolve_locale(locale)
        if user is None:
            user = RichUser()
        if isinstance(user, Bootstrappable | Shutdownable):
            self.life_cycle.on_bootstrap(lambda: self.life_cycle.synchronize(user))
        self._user = user
        self._cache_directory = (
            Path(environ.get("BETTY_CACHE_DIRECTORY", CACHE_DIRECTORY))
            if cache_directory is None
            else cache_directory
        )

    async def _bootstrap_localizer(self) -> None:
        self._user.localizer = await self.localizer

    @override
    @classmethod
    def new_data_cls(cls) -> type[AppConfiguration]:
        return AppConfiguration

    @override
    @classmethod
    async def new(cls, services: ServiceLevel, data: AppConfiguration, /) -> Self:
        return cls(locale=data.locale)

    @classmethod
    @asynccontextmanager
    async def new_from_environment(cls) -> AsyncIterator[Self]:
        """
        Create a new application from the environment.
        """
        if AppConfiguration.FILE.exists():
            configuration = AppConfiguration.data().porter.load(
                (await assert_load_file())(AppConfiguration.FILE)
            )
            app = await cls.new(UNIVERSE, configuration)
        else:
            app = cls()
        async with app:
            yield app

    @classmethod
    @asynccontextmanager
    async def new_isolated(
        cls,
        *,
        cache_directory: Path | None = None,
        cache: TypedSynchronousServiceOrFactory[App, Cache[Any]] | None = None,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
        process_pool: TypedSynchronousServiceOrFactory[App, futures.ProcessPoolExecutor]
        | None = None,
        user: User | None = None,
        translations: TypedAsynchronousServiceOrFactory[App, TranslationRepository]
        | None
        | Literal[False] = False,
    ) -> AsyncIterator[Self]:
        """
        Create a new, isolated, temporary application.

        The application will not use any persistent caches, or leave
        any traces on the system.
        """
        async with AsyncExitStack() as exit_stack:
            if cache_directory is None:
                cache_directory = Path(
                    await to_thread(mkdtemp),  # ty:ignore[invalid-argument-type]
                )
                exit_stack.push_async_callback(to_thread, rmtree, cache_directory)
            async with cls(
                cache_directory=cache_directory,
                cache=NoOpCache() if cache is None else cache,
                plugins=plugins,
                process_pool=process_pool,
                user=NoOpUser() if user is None else user,
                translations=DEFAULT_TRANSLATION_REPOSITORY
                if translations is False
                else translations,
            ) as app:
                yield app

    @property
    def user(self) -> User:
        """
        The current user session.
        """
        return self._user

    @service
    async def translations(self) -> TranslationRepository:
        """
        The available translations.
        """
        return AssetTranslationRepository(self.assets, self.binary_file_cache)

    @service
    async def localizer(self) -> Localizer:
        """
        Get the application's user-facing localizer.
        """
        return (await self.localizers).get(self._locale)

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
        http_client: aiohttp.ClientSession = CachedSession(
            cache=FileBackend(self.binary_file_cache.with_scope("http-client").path),
            headers={
                "User-Agent": "Betty (https://betty.readthedocs.io/)",
            },
            middlewares=[
                ClientErrorToUserMessageMiddleware(self.user),
                RateLimitMiddleware(self.rate_limits),
            ],
        )

        self.life_cycle.on_shutdown(lambda wait: http_client.close())

        return http_client

    @service
    def cache(self) -> Cache[Any]:
        """
        The cache.
        """
        return PickledFileCache[Any](self._cache_directory)

    @service
    def binary_file_cache(self) -> BinaryFileCache:
        """
        The binary file cache.
        """
        return BinaryFileCache(self._cache_directory)

    @service
    def process_pool(self) -> futures.ProcessPoolExecutor:
        """
        The shared process pool.

        Use this to run CPU/computationally-heavy tasks in other processes.
        """
        process_pool = ProcessPoolExecutor()
        self.life_cycle.on_shutdown(
            lambda wait: process_pool.shutdown(wait, cancel_futures=not wait)
        )
        return process_pool
