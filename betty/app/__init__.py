"""Define Betty's core application functionality."""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, cast, final

from aiofiles.tempfile import TemporaryDirectory
from aiohttp_client_cache.backends.filesystem import FileBackend
from aiohttp_client_cache.session import CachedSession
from typing_extensions import TypeVar, override

import betty
import betty.dirs
from betty.app import config
from betty.app.config import AppConfiguration
from betty.app.factory import AppDependentFactory, AppDependentSelfFactory
from betty.asset import AssetRepository, StaticAssetRepository
from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.cache.no_op import NoOpCache
from betty.config import Configurable
from betty.dirs import CACHE_DIRECTORY_PATH
from betty.factory import Target, new_target
from betty.http_client import ClientErrorToUserMessageMiddleware
from betty.http_client.rate_limit import RateLimitDefinition, RateLimitMiddleware
from betty.license import LicenseDefinition
from betty.license.licenses import SpdxLicenseBuilder
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localize import Localizer, LocalizerRepository
from betty.locale.translation import (
    AssetTranslationRepository,
    NoOpTranslationRepository,
    TranslationRepository,
)
from betty.multiprocessing import ProcessPoolExecutor
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.ordered import sort_ordered_plugin_graph
from betty.plugin.repository.provider import PluginRepositoryProvider
from betty.plugin.repository.provider.service import (
    ServiceLevelPluginRepositoryProvider,
)
from betty.plugin.repository.static import StaticPluginRepository
from betty.requirement import Requirement, StaticRequirement
from betty.serde.file import assert_load_file
from betty.service.container import (
    ServiceContainer,
    ServiceFactory,
    StaticService,
    service,
)
from betty.typing import threadsafe
from betty.user.no_op import NoOpUser

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from concurrent import futures

    import aiohttp

    from betty.cache import Cache
    from betty.locale.localizable import LocalizableLike
    from betty.machine_name import MachineName
    from betty.plugin.repository import PluginRepository
    from betty.service.level import ServiceLevel
    from betty.service.level.factory import AnyFactoryTarget
    from betty.user import User

_T = TypeVar("_T")
_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
@threadsafe
class App(Configurable[AppConfiguration], ServiceContainer, PluginRepositoryProvider):
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
        process_pool: futures.ProcessPoolExecutor | None = None,
        translations: TranslationRepository | None = None,
    ):
        from betty.rich.user import RichUser

        cls = type(self)
        super().__init__(configuration=configuration)
        self._user = user or RichUser()
        if process_pool is not None:
            cls.process_pool.override(self, process_pool)
        if translations is not None:
            cls.translations.override(self, translations)
        self._cache_directory_path = cache_directory_path
        cls.cache.override_factory(self, cache_factory)
        self._plugin_repository_provider = ServiceLevelPluginRepositoryProvider(self)

    @override
    @classmethod
    def configuration_cls(cls) -> type[AppConfiguration]:
        return AppConfiguration

    @override
    @classmethod
    async def requires(
        cls, services: ServiceLevel, subject: LocalizableLike, /
    ) -> Requirement | Self:
        if services is None:
            return StaticRequirement(
                _("{subject} requires a running app.").format(subject=subject)
            )
        return services if isinstance(services, App) else services.app

    @override
    async def plugins(
        self,
        plugin_type: type[_PluginDefinitionT] | MachineName,
        *,
        check_requirements: bool = True,
    ) -> PluginRepository[_PluginDefinitionT]:
        return await self._plugin_repository_provider.plugins(
            plugin_type, check_requirements=check_requirements
        )

    @classmethod
    @asynccontextmanager
    async def new_from_environment(cls) -> AsyncIterator[Self]:
        """
        Create a new application from the environment.
        """
        if config.CONFIGURATION_FILE_PATH.exists():
            configuration = AppConfiguration.load(
                (await assert_load_file())(config.CONFIGURATION_FILE_PATH)
            )
        else:
            configuration = AppConfiguration()
        yield cls(
            configuration,
            Path(environ.get("BETTY_CACHE_DIRECTORY", CACHE_DIRECTORY_PATH)),
            cache_factory=lambda app: PickledFileCache[Any](app._cache_directory_path),
        )

    @classmethod
    @asynccontextmanager
    async def new_isolated(
        cls,
        *,
        cache_directory_path: Path | None = None,
        cache_factory: ServiceFactory[Self, Cache[Any]] | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
        user: User | None = None,
        translations: TranslationRepository | None | False = False,
    ) -> AsyncIterator[Self]:
        """
        Create a new, isolated, temporary application.

        The application will not use any persistent caches, or leave
        any traces on the system.
        """
        async with AsyncExitStack() as exit_stack:
            if cache_directory_path is None:
                cache_directory_path = Path(
                    await exit_stack.enter_async_context(TemporaryDirectory())
                )
            yield cls(
                AppConfiguration(),
                cache_directory_path,
                cache_factory=cache_factory or StaticService(NoOpCache()),
                process_pool=process_pool,
                user=NoOpUser() if user is None else user,
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
        http_rate_limits = await self.plugins(RateLimitDefinition)
        rate_limit_sorter = await sort_ordered_plugin_graph(
            http_rate_limits, http_rate_limits
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
                        await self.new_target(http_rate_limits[rate_limit_id].cls)
                        for rate_limit_id in rate_limit_sorter.static_order()
                    ]
                ),
            ],
        )

        async def _shutdown(wait: bool) -> None:
            await http_client.close()

        self._shutdown_stack.append(_shutdown)

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
    async def new_target(self, target: AnyFactoryTarget[_T]) -> _T:
        if (
            isinstance(target, AppDependentFactory)
            or isinstance(target, type)
            and issubclass(target, AppDependentSelfFactory)
        ):
            return cast(_T, await target.new_for_app(self))
        return await new_target(cast(Target[_T], target))

    @service
    async def _spdx_license_repository(self) -> PluginRepository[LicenseDefinition]:
        return StaticPluginRepository(
            LicenseDefinition,
            *[
                license
                async for license in SpdxLicenseBuilder(  # noqa A001
                    binary_file_cache=self.binary_file_cache.with_scope("spdx"),
                    http_client=await self.http_client,
                    user=self.user,
                ).build()
            ],
        )
