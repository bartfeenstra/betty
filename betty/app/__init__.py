"""Define Betty's core application functionality."""

from __future__ import annotations

from contextlib import asynccontextmanager
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast, final

from aiofiles.tempfile import TemporaryDirectory
from aiohttp_client_cache.backends.filesystem import FileBackend
from aiohttp_client_cache.session import CachedSession
from typing_extensions import override

import betty
from betty import about
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
from betty.http_client import ClientErrorToUserMessageMiddleware
from betty.http_client.rate_limit import RateLimitDefinition, RateLimitMiddleware
from betty.license import LicenseDefinition
from betty.license.licenses import SpdxLicenseBuilder
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import Localizer, LocalizerRepository
from betty.locale.translation import (
    AssetTranslationRepository,
    NoOpTranslationRepository,
    TranslationRepository,
)
from betty.model import EntityDefinition
from betty.multiprocessing import ProcessPoolExecutor
from betty.plugin import sort_ordered_plugin_graph
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.project.extension import ExtensionDefinition
from betty.render import RendererDefinition
from betty.service import ServiceFactory, ServiceProvider, StaticService, service
from betty.typing import threadsafe

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from concurrent import futures

    import aiohttp

    from betty.cache import Cache
    from betty.console.command import CommandDefinition
    from betty.plugin import PluginRepository
    from betty.user import User

_T = TypeVar("_T")


@final
@threadsafe
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
        process_pool: futures.ProcessPoolExecutor | None = None,
        translations: TranslationRepository | None = None,
        entity_type_repository: PluginRepository[EntityDefinition] | None = None,
        extension_repository: PluginRepository[ExtensionDefinition] | None = None,
        command_repository: PluginRepository[CommandDefinition] | None = None,
        renderer_repository: PluginRepository[RendererDefinition] | None = None,
    ):
        from betty.console.user import ConsoleUser

        cls = type(self)
        super().__init__(configuration=configuration)
        self._user = user or ConsoleUser()
        if process_pool is not None:
            cls.process_pool.override(self, process_pool)
        if translations is not None:
            cls.translations.override(self, translations)
        if entity_type_repository is not None:
            cls.entity_type_repository.override(self, entity_type_repository)
        if extension_repository is not None:
            cls.extension_repository.override(self, extension_repository)
        if command_repository is not None:
            cls.command_repository.override(self, command_repository)
        if renderer_repository is not None:
            cls.renderer_repository.override(self, renderer_repository)
        self._cache_directory_path = cache_directory_path
        cls.cache.override_factory(self, cache_factory)

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
        process_pool: futures.ProcessPoolExecutor | None = None,
        user: User | None = None,
        translations: TranslationRepository | None | False = False,
        entity_type_repository: PluginRepository[EntityDefinition] | None = None,
        extension_repository: PluginRepository[ExtensionDefinition] | None = None,
        command_repository: PluginRepository[CommandDefinition] | None = None,
        renderer_repository: PluginRepository[RendererDefinition] | None = None,
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
                process_pool=process_pool,
                user=user,
                translations=NoOpTranslationRepository()
                if translations is False
                else translations,
                entity_type_repository=entity_type_repository,
                extension_repository=extension_repository,
                command_repository=command_repository,
                renderer_repository=renderer_repository,
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
    def http_rate_limit_repository(self) -> PluginRepository[RateLimitDefinition]:
        """
        The rate limit plugin repository.

        Read more about :doc:`/development/plugin/http-rate-limit`.
        """
        return EntryPointPluginRepository(RateLimitDefinition, "betty.http_rate_limit")

    @service
    async def http_client(self) -> aiohttp.ClientSession:
        """
        The HTTP client.
        """
        rate_limit_sorter = await sort_ordered_plugin_graph(
            self.http_rate_limit_repository, self.http_rate_limit_repository
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
                        await self.new_target(
                            self.http_rate_limit_repository[rate_limit_id].cls
                        )
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
        raise NotImplementedError

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
    def entity_type_repository(self) -> PluginRepository[EntityDefinition]:
        """
        The entity types available to this application.

        Read more about :doc:`/development/plugin/entity-type`.
        """
        return EntryPointPluginRepository(EntityDefinition, "betty.entity_type")

    @service
    def extension_repository(self) -> PluginRepository[ExtensionDefinition]:
        """
        The extensions available to this application.

        Read more about :doc:`/development/plugin/extension`.
        """
        return EntryPointPluginRepository(ExtensionDefinition, "betty.extension")

    @service
    def command_repository(self) -> PluginRepository[CommandDefinition]:
        """
        The console commands available to this application.

        Read more about :doc:`/development/plugin/command`.
        """
        from betty.console.command import CommandDefinition

        return ProxyPluginRepository(
            CommandDefinition,
            EntryPointPluginRepository(CommandDefinition, "betty.command"),
            *(
                [EntryPointPluginRepository(CommandDefinition, "betty.dev.command")]
                if about.IS_DEVELOPMENT
                else []
            ),
        )

    @service
    def renderer_repository(self) -> PluginRepository[RendererDefinition]:
        """
        The renderers available to this application.

        Read more about :doc:`/development/plugin/renderer`.
        """
        return EntryPointPluginRepository(RendererDefinition, "betty.renderer")

    @service
    async def spdx_license_repository(self) -> PluginRepository[LicenseDefinition]:
        """
        The SPDX licenses available to this application.
        """
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
