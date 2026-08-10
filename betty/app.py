"""Define Betty's core application functionality."""

from __future__ import annotations

from asyncio import gather, to_thread
from concurrent import futures
from contextlib import AsyncExitStack, asynccontextmanager
from os import environ
from shutil import rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any, Final, Self, final

from aiohttp_client_cache.backends.filesystem import FileBackend
from aiohttp_client_cache.session import CachedSession

from betty import about
from betty.asyncio import ResolvableAwaitable, resolve_await
from betty.attrs.locale import new_locale_attr
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.dirs import app_config_directory, cache_directory
from betty.gettext import TranslationsRepository
from betty.http_client import ClientErrorToUserMessageMiddleware
from betty.http_client.rate_limit import RateLimitDefinition, RateLimitMiddleware
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.locale import ResolvableLocale, default_locale
from betty.localizables.gettext import _
from betty.localizer import LocalizerRepository
from betty.media_type import MediaTypeDefinition
from betty.multiprocessing import ProcessPoolExecutor
from betty.portable.file import assert_load_file
from betty.prop import HasProps
from betty.requirements.service_level import RequirableServiceLevel
from betty.rich.user import RichUser
from betty.sample import Sample, Size
from betty.serialize import SerializerDefinition
from betty.service import Service
from betty.service_level import ServiceLevel
from betty.services.asset import AssetRepositoryService
from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.collection.keyed import PluginDefinitionsService
from betty.services.plugin.instance.collection.keyed import PluginInstancesService
from betty.services.simple import service
from betty.store import TransientStore
from betty.stores.file import TransientBinaryFileStore, TransientPickledFileStore
from betty.stores.no_op import NoOpStore
from betty.user import User
from betty.user.no_op import NoOpUser

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterable, Mapping
    from pathlib import Path

    import aiohttp
    from babel import Locale

    from betty.asset import AssetDirectoryDefinition
    from betty.pathlib import StrPath
    from betty.plugin import PluginDefinition
    from betty.plugin.discovery import ResolvableDiscovery
    from betty.plugin.resolve import ResolvablePluginDefinition
    from betty.service_level import Plugins
    from betty.services.plugin import SupportedPlugins
    from betty.services.simple.synchronous import TypedSynchronousServiceOrFactory


class _AppBootstrapServiceLevel(ServiceLevel, HasPluginServices):
    serializers = PluginInstancesService(SerializerDefinition)


@final
class App(RequirableServiceLevel, HasPluginServices):
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
        binary_file_cache: TypedSynchronousServiceOrFactory[
            App, TransientBinaryFileStore
        ],
        assets: Iterable[ResolvablePluginDefinition[AssetDirectoryDefinition]] = (),
        cache: TypedSynchronousServiceOrFactory[App, TransientStore[Any]] | None = None,
        media_types: Iterable[ResolvablePluginDefinition[MediaTypeDefinition]] = (),
        plugins: Plugins | None = None,
        process_pool: TypedSynchronousServiceOrFactory[App, futures.ProcessPoolExecutor]
        | None = None,
        rate_limits: Iterable[RateLimitDefinition] = (),
        serializers: Iterable[ResolvablePluginDefinition[SerializerDefinition]] = (),
        supported_plugins: SupportedPlugins = (),
        user: User | Callable[[App], ResolvableAwaitable[User]] | None = None,
    ):
        cls = type(self)
        cls.binary_file_cache.override(
            self,
            Service(binary_file_cache)
            if isinstance(binary_file_cache, TransientBinaryFileStore)
            else binary_file_cache,
        )
        if process_pool is not None:
            cls.process_pool.override(
                self,
                Service(process_pool)
                if isinstance(process_pool, futures.ProcessPoolExecutor)
                else process_pool,
            )
        if cache is not None:
            cls.cache.override(
                self, Service(cache) if isinstance(cache, TransientStore) else cache
            )
        super().__init__(plugins=plugins, supported_plugins=supported_plugins)
        cls.asset_directories.add_init_plugins(self, *assets)
        cls.media_types.add_init_plugins(self, *media_types)
        cls.rate_limits.add_init_plugins(self, *rate_limits)
        cls.serializers.add_init_plugins(self, *serializers)
        self._user: User
        if user is None:
            self.life_cycle.on_bootstrap(self._set_default_user)
        elif isinstance(user, User):
            self._user = user
            if isinstance(user, Bootstrappable | Shutdownable):
                self.life_cycle.on_bootstrap(lambda: self.life_cycle.synchronize(user))
        else:
            self.life_cycle.on_bootstrap(lambda: self._set_user(user))

    async def _set_default_user(self) -> None:
        self._user = RichUser()

    async def _set_user(self, user: Callable[[App], ResolvableAwaitable[User]]) -> None:
        self._user = await resolve_await(user(self))
        if isinstance(user, Bootstrappable | Shutdownable):
            await self.life_cycle.synchronize(self._user)

    @property
    def user(self) -> User:
        """
        The current user session.
        """
        return self._user

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
                    ),
                )
                locale = data.locale
        else:
            locale = None
        app_cache_directory = environ.get("BETTY_CACHE_DIRECTORY", cache_directory)
        async with cls(
            cache=TransientPickledFileStore(app_cache_directory),
            binary_file_cache=TransientBinaryFileStore(app_cache_directory),
            user=lambda app: cls._new_from_environment_user(app, locale),
        ) as app:
            yield app

    @classmethod
    async def _new_from_environment_user(
        cls, app: App, locale: Locale | None, /
    ) -> User:
        return RichUser(
            localizer=await app.localizers.get(locale or User.default_locale)
        )

    @classmethod
    @asynccontextmanager
    async def new_isolated(
        cls,
        *,
        binary_file_cache_directory: StrPath | None = None,
        cache: TypedSynchronousServiceOrFactory[App, TransientStore[Any]] | None = None,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
        process_pool: TypedSynchronousServiceOrFactory[App, futures.ProcessPoolExecutor]
        | None = None,
        user: User | None = None,
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
                binary_file_cache=TransientBinaryFileStore(binary_file_cache_directory),
                cache=NoOpStore() if cache is None else cache,
                plugins=plugins,
                process_pool=process_pool,
                user=NoOpUser() if user is None else user,
            ) as app:
                yield app

    @service
    def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        return LocalizerRepository(
            translations=TranslationsRepository(
                assets=self.asset_directories, cache=self.binary_file_cache
            )
        )

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
                "User-Agent": f"Betty ({about.url})",
            },
            middlewares=[
                ClientErrorToUserMessageMiddleware(self.user),
                RateLimitMiddleware(self.rate_limits),
            ],
        )

        self.life_cycle.on_shutdown(lambda wait: http_client.close())

        return http_client

    @service
    def cache(self) -> TransientStore[Any]:
        """
        The cache.
        """
        return NoOpStore()

    @service
    def binary_file_cache(self) -> TransientBinaryFileStore:
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
        self.locale = locale
