"""Define Betty's core application functionality."""

from __future__ import annotations

from asyncio import gather, to_thread
from concurrent import futures
from contextlib import AsyncExitStack, asynccontextmanager
from os import environ
from shutil import rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any, Final, Literal, Self, final

from aiohttp_client_cache.backends.filesystem import FileBackend
from aiohttp_client_cache.session import CachedSession

from betty.asset import AssetRepositoryService
from betty.attrs.locale import new_locale_attr
from betty.cache import Cache
from betty.caches.file import BinaryFileCache, PickledFileCache
from betty.caches.no_op import NoOpCache
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.dirs import app_config_directory, cache_directory
from betty.http_client import ClientErrorToUserMessageMiddleware
from betty.http_client.rate_limit import RateLimitDefinition, RateLimitMiddleware
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.locale import ResolvableLocale, default_locale, resolve_locale
from betty.locale.localizable.gettext import _
from betty.locale.localize import Localizer, LocalizerRepository
from betty.locale.translation import (
    AssetTranslationRepository,
    TranslationRepository,
    default_translation_repository,
)
from betty.media_type import MediaTypeDefinition
from betty.multiprocessing import ProcessPoolExecutor
from betty.portable.file import assert_load_file
from betty.prop import HasProps
from betty.requirements.service_level import RequirableServiceLevel
from betty.rich.user import RichUser
from betty.sample import Sample, Size
from betty.serialize import SerializerDefinition
from betty.service import Service
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.definition.collection.keyed import PluginDefinitionsService
from betty.service.plugin.instance.collection.keyed import PluginInstancesService
from betty.service.simple import service
from betty.service_level import ServiceLevel
from betty.typing import threadsafe
from betty.user.no_op import NoOpUser

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable, Mapping
    from pathlib import Path

    import aiohttp

    from betty.asset import AssetDirectoryDefinition
    from betty.pathlib import StrPath
    from betty.plugin import PluginDefinition
    from betty.plugin.discovery import ResolvableDiscovery
    from betty.plugin.resolve import ResolvablePluginDefinition
    from betty.service.plugin import SupportedPlugins
    from betty.service.simple.asynchronous import TypedAsynchronousServiceOrFactory
    from betty.service.simple.synchronous import TypedSynchronousServiceOrFactory
    from betty.service_level import Plugins
    from betty.user import User


class _AppBootstrapServiceLevel(ServiceLevel, PluginServiceProvider):
    serializers = PluginInstancesService(SerializerDefinition)


@final
@threadsafe
class App(RequirableServiceLevel, PluginServiceProvider):
    """
    The Betty application.

    .. list-table::
       :widths: 20 10
       :header-rows: 0

       * - Configuration
         - :py:class:`betty.app.AppData`
    """

    asset_directories = AssetRepositoryService()

    media_types = PluginDefinitionsService(MediaTypeDefinition)

    rate_limits = PluginDefinitionsService(RateLimitDefinition)

    serializers = PluginInstancesService(SerializerDefinition)

    def __init__(
        self,
        *,
        binary_file_cache: TypedSynchronousServiceOrFactory[App, BinaryFileCache],
        assets: Iterable[ResolvablePluginDefinition[AssetDirectoryDefinition]] = (),
        cache: TypedSynchronousServiceOrFactory[App, Cache[Any]] | None = None,
        locale: ResolvableLocale | None = None,
        meda_types: Iterable[ResolvablePluginDefinition[MediaTypeDefinition]] = (),
        plugins: Plugins | None = None,
        process_pool: TypedSynchronousServiceOrFactory[App, futures.ProcessPoolExecutor]
        | None = None,
        rate_limits: Iterable[RateLimitDefinition] = (),
        serializers: Iterable[ResolvablePluginDefinition[SerializerDefinition]] = (),
        supported_plugins: SupportedPlugins = (),
        translations: TypedAsynchronousServiceOrFactory[App, TranslationRepository]
        | None = None,
        user: User | None = None,
    ):
        cls = type(self)
        cls.binary_file_cache.override(
            self,
            Service(binary_file_cache)
            if isinstance(binary_file_cache, BinaryFileCache)
            else binary_file_cache,
        )
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
        super().__init__(plugins=plugins, supported_plugins=supported_plugins)
        cls.asset_directories.add_init_plugins(self, *assets)
        cls.media_types.add_init_plugins(self, *meda_types)
        cls.rate_limits.add_init_plugins(self, *rate_limits)
        cls.serializers.add_init_plugins(self, *serializers)
        self.life_cycle.on_bootstrap(self._bootstrap_localizer)
        self._locale = default_locale if locale is None else resolve_locale(locale)
        if user is None:
            user = RichUser()
        if isinstance(user, Bootstrappable | Shutdownable):
            self.life_cycle.on_bootstrap(lambda: self.life_cycle.synchronize(user))
        self.user: Final[User] = user
        """
        The current user session.
        """

    async def _bootstrap_localizer(self) -> None:
        self.user.localizer = await self.localizer

    @classmethod
    @asynccontextmanager
    async def new_from_environment(cls) -> AsyncIterator[Self]:
        """
        Create a new application from the environment.
        """
        if AppData.FILE.exists():
            async with _AppBootstrapServiceLevel() as services:
                data = AppData.data().porter.load(
                    assert_load_file(serializers=await gather(*services.serializers))(
                        AppData.FILE
                    )
                )
                locale = data.locale
        else:
            locale = None
        app_cache_directory = environ.get("BETTY_CACHE_DIRECTORY", cache_directory)
        async with cls(
            cache=PickledFileCache(app_cache_directory),
            binary_file_cache=BinaryFileCache(app_cache_directory),
            locale=locale,
        ) as app:
            yield app

    @classmethod
    @asynccontextmanager
    async def new_isolated(
        cls,
        *,
        binary_file_cache_directory: StrPath | None = None,
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
            if binary_file_cache_directory is None:
                binary_file_cache_directory: StrPath = await to_thread(
                    mkdtemp,
                )  # ty:ignore[invalid-assignment]
                exit_stack.push_async_callback(
                    to_thread, rmtree, binary_file_cache_directory
                )
            async with cls(
                binary_file_cache=BinaryFileCache(binary_file_cache_directory),
                cache=NoOpCache() if cache is None else cache,
                plugins=plugins,
                process_pool=process_pool,
                user=NoOpUser() if user is None else user,
                translations=default_translation_repository
                if translations is False
                else translations,
            ) as app:
                yield app

    @service
    async def translations(self) -> TranslationRepository:
        """
        The available translations.
        """
        return AssetTranslationRepository(
            self.asset_directories, self.binary_file_cache
        )

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
            cache=FileBackend(
                self.binary_file_cache.with_scope("http-client").directory
            ),
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
        return NoOpCache()

    @service
    def binary_file_cache(self) -> BinaryFileCache:
        """
        The binary file cache.
        """
        raise NotImplementedError("This service MUST always be explicitly overridden.")

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


@final
@ObjectDefinition(
    label=_("Application configuration"),
    samples=[
        lambda: Sample(AppData(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(AppData(locale=default_locale), label="Full", size=Size.FULL),
    ],
)
class AppData(Data, HasProps):
    """
    Configuration for :py:class:`betty.app.App`.

    .. data:: betty.app:AppData
    """

    FILE: Final[Path] = app_config_directory / "app.json"

    locale = new_locale_attr().optional
    """
    The application locale.
    """

    def __init__(self, *, locale: ResolvableLocale | None = None):
        super().__init__()
        self.locale = None if locale is None else resolve_locale(locale)
