"""Define Betty's core application functionality."""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Self, final, override

from aiofiles.tempfile import TemporaryDirectory
from aiohttp_client_cache.backends.filesystem import FileBackend
from aiohttp_client_cache.session import CachedSession

import betty
import betty.dirs
from betty.app.data import AppConfiguration
from betty.asset import AssetRepository, StaticAssetRepository
from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.cache.no_op import NoOpCache
from betty.dirs import CACHE_DIRECTORY_PATH
from betty.http_client import ClientErrorToUserMessageMiddleware
from betty.http_client.rate_limit import RateLimitDefinition, RateLimitMiddleware
from betty.life_cycle import LifeCycle
from betty.life_cycle.manage import ManagedLifeCycle
from betty.locale import DEFAULT_LOCALE, ResolvableLocale, resolve_locale
from betty.locale.localize import Localizer, LocalizerRepository
from betty.locale.translation import (
    DEFAULT_TRANSLATION_REPOSITORY,
    AssetTranslationRepository,
    TranslationRepository,
)
from betty.multiprocessing import ProcessPoolExecutor
from betty.plugin.ordered import sort_ordered_plugin_graph
from betty.portable.file import assert_load_file
from betty.service.factory import DataManufacturable
from betty.service.level import UNIVERSE, ServiceLevel
from betty.service.provider import ServiceFactory, service
from betty.typing import threadsafe
from betty.user.no_op import NoOpUser

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable, Mapping
    from concurrent import futures

    import aiohttp

    from betty.cache import Cache
    from betty.plugin import PluginDefinition, ResolvableDiscovery
    from betty.user import User


@final
@threadsafe
class App(DataManufacturable[AppConfiguration], ServiceLevel, ManagedLifeCycle):
    """
    The Betty application.

    .. list-table::
       :widths: 20 10
       :header-rows: 0

       * - Configuration
         - :py:class:`betty.app.data.AppConfiguration`
    """

    def __init__(
        self,
        *,
        cache_directory: Path | None = None,
        cache_factory: ServiceFactory[App, Cache[Any]] | None = None,
        locale: ResolvableLocale | None = None,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
        translations: TranslationRepository | None = None,
        user: User | None = None,
    ):
        from betty.rich.user import RichUser

        cls = type(self)
        super().__init__(plugins=plugins)
        self.life_cycle.on_bootstrap(self._bootstrap_localizer)
        self._locale = DEFAULT_LOCALE if locale is None else resolve_locale(locale)
        self._user = user or RichUser()
        if isinstance(self._user, LifeCycle):
            self.life_cycle.attach(self._user)
        if process_pool is not None:
            cls.process_pool.override(self, process_pool)
        if translations is not None:
            cls.translations.override(self, translations)
        self._cache_directory = (
            Path(environ.get("BETTY_CACHE_DIRECTORY", CACHE_DIRECTORY_PATH))
            if cache_directory is None
            else cache_directory
        )
        cls.cache.override_factory(
            self,
            (lambda _: PickledFileCache[Any](self._cache_directory))
            if cache_factory is None
            else cache_factory,
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
    async def new_from_environment(cls) -> Self:
        """
        Create a new application from the environment.
        """
        if AppConfiguration.FILE.exists():
            configuration = AppConfiguration.data().porter.load(
                (await assert_load_file())(AppConfiguration.FILE)
            )
            return await cls.new(UNIVERSE, configuration)
        return cls()

    @classmethod
    @asynccontextmanager
    async def new_isolated(
        cls,
        *,
        cache_directory: Path | None = None,
        cache_factory: ServiceFactory[App, Cache[Any]] | None = None,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
        user: User | None = None,
        translations: TranslationRepository | None | Literal[False] = False,
    ) -> AsyncIterator[Self]:
        """
        Create a new, isolated, temporary application.

        The application will not use any persistent caches, or leave
        any traces on the system.
        """
        async with AsyncExitStack() as exit_stack:
            if cache_directory is None:
                cache_directory = Path(
                    await exit_stack.enter_async_context(TemporaryDirectory())
                )
            yield cls(
                cache_directory=cache_directory,
                cache_factory=(lambda _: NoOpCache())
                if cache_factory is None
                else cache_factory,
                plugins=plugins,
                process_pool=process_pool,
                user=NoOpUser() if user is None else user,
                translations=DEFAULT_TRANSLATION_REPOSITORY
                if translations is False
                else translations,
            )

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
        return StaticAssetRepository(betty.dirs.ASSETS_DIRECTORY_PATH)

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
        http_rate_limits = self.plugins[RateLimitDefinition]
        rate_limit_sorter = await sort_ordered_plugin_graph(
            http_rate_limits, [x async for x in http_rate_limits]
        )

        http_client: aiohttp.ClientSession = CachedSession(
            cache=FileBackend(self.binary_file_cache.with_scope("http-client").path),
            headers={
                "User-Agent": "Betty (https://betty.readthedocs.io/)",
            },
            middlewares=[
                ClientErrorToUserMessageMiddleware(self.user),
                RateLimitMiddleware(
                    [
                        await self.factory.new(
                            (await http_rate_limits[rate_limit_id]).cls
                        )
                        for rate_limit_id in rate_limit_sorter.static_order()
                    ]
                ),
            ],
        )

        self.life_cycle.on_shutdown(lambda wait: http_client.close())

        return http_client

    @service
    def cache(self) -> Cache[Any]:
        """
        The cache.
        """
        raise Exception(
            "This must never happen, because a cache must be set explicitly."
        )

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
