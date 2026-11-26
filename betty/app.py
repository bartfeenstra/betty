"""Define Betty's core application functionality."""

from __future__ import annotations

from asyncio import to_thread
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
from betty.collections.mapping.dict import empty_frozen_dict
from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.dirs import app_config_directory, cache_directory
from betty.freezers.attr import AttrFreezable
from betty.gettext import TranslationsRepository
from betty.http_client import (
    ClientErrorToUserMessageMiddleware,
    RateLimitDefinition,
    RateLimitMiddleware,
)
from betty.image import Imager
from betty.life_cycle import Bootstrappable, Shutdownable
from betty.locale import ResolvableLocale, default_locale
from betty.localizables.gettext import _
from betty.localizer import LocalizerRepository
from betty.portable.file import assert_load_file
from betty.requirements.service_level import RequirableServiceLevel
from betty.sample import Sample, Size
from betty.serialize import SerializerDefinition
from betty.serializers.json import Json
from betty.service import Service
from betty.services.asset import HasAssets
from betty.services.content_type import HasContentTypes
from betty.services.plugin.definition.collection.catalog import PluginDefinitionsService
from betty.services.plugin.instance.collection.catalog import PluginInstancesService
from betty.services.simple import service
from betty.stores.file import TransientBinaryFileStore, TransientPickledFileStore
from betty.stores.no_op import NoOpStore
from betty.typing import Unreachable
from betty.uis.console import Console
from betty.uis.no_op import NoOpUi
from betty.user.ui import Ui

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from pathlib import Path

    import aiohttp
    from babel import Locale

    from betty.pathlib import StrPath
    from betty.service_level import PluginDiscoveries
    from betty.services.plugin import SupportPlugins
    from betty.services.simple.synchronous import TypedSynchronousServiceOrFactory
    from betty.store import TransientStore


@final
class App(RequirableServiceLevel, HasAssets, HasContentTypes):
    """
    The Betty application.

    .. list-table::
       :widths: 20 10
       :header-rows: 0

       * - Configuration
         - :py:class:`betty.app.AppConfig`
    """

    rate_limits = PluginDefinitionsService(RateLimitDefinition)
    serializers = PluginInstancesService(SerializerDefinition)

    def __init__(
        self,
        *,
        binary_file_cache: TypedSynchronousServiceOrFactory[
            App, TransientBinaryFileStore
        ],
        plugins: PluginDiscoveries = empty_frozen_dict,
        support: SupportPlugins = (),
        ui: Ui | Callable[[App], ResolvableAwaitable[Ui]] | None = None,
    ):
        cls = type(self)
        cls.binary_file_cache.override(
            self,
            Service(binary_file_cache)
            if isinstance(binary_file_cache, TransientBinaryFileStore)
            else binary_file_cache,
        )
        super().__init__(plugin_discoveries=plugins, support_plugins=support)
        self._ui: Ui
        if ui is None:
            self.life_cycle.on_bootstrap(self._set_default_ui)
        elif isinstance(ui, Ui):
            self._ui = ui
            if isinstance(ui, Bootstrappable | Shutdownable):
                self.life_cycle.on_bootstrap(lambda: self.life_cycle.bind(ui))
        else:
            self.life_cycle.on_bootstrap(lambda: self._set_ui(ui))

    async def _set_default_ui(self) -> None:
        self._ui = Console()

    async def _set_ui(self, ui: Callable[[App], ResolvableAwaitable[Ui]], /) -> None:
        self._ui = await resolve_await(ui(self))
        if isinstance(ui, Bootstrappable | Shutdownable):
            await self.life_cycle.bind(self._ui)

    @property
    def ui(self) -> Ui:
        """
        The current user interface.
        """
        return self._ui

    @classmethod
    @asynccontextmanager
    async def new_from_environment(cls) -> AsyncGenerator[Self]:
        """
        Create a new application from the environment.
        """
        if AppConfig.file.exists():
            data = AppConfig.definition.porter.load(
                assert_load_file(serializers=[Json()])(AppConfig.file),
            )
            locale = data.locale
        else:
            locale = None
        app_cache_directory = environ.get("BETTY_CACHE_DIRECTORY", cache_directory)
        app = cls(
            binary_file_cache=TransientBinaryFileStore(app_cache_directory),
            ui=lambda app: cls._new_from_environment_user(app, locale),
        )
        cls.cache.override(app, Service(TransientPickledFileStore(app_cache_directory)))
        async with app:
            yield app

    @classmethod
    async def _new_from_environment_user(cls, app: App, locale: Locale | None, /) -> Ui:
        return Console(localizer=await app.localizers.get(locale or Ui.default_locale))

    @classmethod
    @asynccontextmanager
    async def new_isolated(
        cls,
        *,
        binary_file_cache_directory: StrPath | None = None,
        plugins: PluginDiscoveries = empty_frozen_dict,
        ui: Ui | None = None,
    ) -> AsyncGenerator[Self]:
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
            project = cls(
                binary_file_cache=TransientBinaryFileStore(binary_file_cache_directory),
                plugins=plugins,
                ui=NoOpUi() if ui is None else ui,
            )

            cls.cache.override(project, Service(NoOpStore()))
            yield project

    @service
    def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        return LocalizerRepository(
            translations=TranslationsRepository(
                assets=self.assets, cache=self.binary_file_cache
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
                ClientErrorToUserMessageMiddleware(self.ui),
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
        raise Unreachable("this service MUST always be explicitly overridden")

    @service
    async def imager(self) -> Imager:
        """
        The imager.
        """
        return Imager(self.known_content_types)


@final
@ObjectDefinition(
    label=_("Application configuration"),
    samples=(
        Sample(lambda: AppConfig(), label="Minimal", size=Size.MINIMAL),
        Sample(lambda: AppConfig(locale=default_locale), label="Full", size=Size.FULL),
    ),
)
class AppConfig(Object, AttrFreezable):
    """
    Configuration for :py:class:`betty.app.App`.

    .. data:: betty.app:AppConfig
    """

    file: Final[Path] = app_config_directory / "app.json"

    locale = new_locale_attr().optional
    """
    The application locale.
    """

    def __init__(self, *, locale: ResolvableLocale | None = None):
        super().__init__()
        self.locale = locale
