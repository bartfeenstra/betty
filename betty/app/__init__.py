"""Define Betty's core application functionality."""

from __future__ import annotations

import operator
from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import suppress, asynccontextmanager, AsyncExitStack
from functools import reduce
from graphlib import CycleError, TopologicalSorter
from multiprocessing import get_context
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Self, Any, final

import aiohttp
from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

from betty import fs
from betty.app.extension import (
    ListExtensions,
    Extension,
    Extensions,
    build_extension_type_graph,
    CyclicDependencyError,
    ExtensionDispatcher,
    ConfigurableExtension,
)
from betty.asyncio import wait_to_thread
from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.config import Configurable, FileBasedConfiguration
from betty.fetch import Fetcher
from betty.fs import HOME_DIRECTORY_PATH
from betty.assets import AssetRepository
from betty.locale import LocalizerRepository, get_data, DEFAULT_LOCALE, Localizer, Str
from betty.model import Entity, EntityTypeProvider
from betty.model.event_type import (
    EventType,
    EventTypeProvider,
    Birth,
    Baptism,
    Adoption,
    Death,
    Funeral,
    Cremation,
    Burial,
    Will,
    Engagement,
    Marriage,
    MarriageAnnouncement,
    Divorce,
    DivorceAnnouncement,
    Residence,
    Immigration,
    Emigration,
    Occupation,
    Retirement,
    Correspondence,
    Confirmation,
)
from betty.project import Project
from betty.render import Renderer, SequentialRenderer
from betty.serde.dump import minimize, void_none, Dump, VoidableDump
from betty.serde.load import (
    AssertionFailed,
    OptionalField,
    assert_record,
    assert_setattr,
    assert_str,
)
from betty.warnings import deprecate

if TYPE_CHECKING:
    from betty.cache import Cache
    from betty.dispatch import Dispatcher
    from types import TracebackType
    from collections.abc import AsyncIterator
    from betty.jinja2 import Environment
    from betty.url import StaticUrlGenerator, LocalizedUrlGenerator

CONFIGURATION_DIRECTORY_PATH = fs.HOME_DIRECTORY_PATH / "configuration"


class _AppExtensions(ListExtensions):
    def __init__(self):
        super().__init__([])

    def _update(self, extensions: list[list[Extension]]) -> None:
        self._extensions = extensions


class AppConfiguration(FileBasedConfiguration):
    """
    Provide configuration for :py:class:`betty.app.App`.
    """

    def __init__(
        self,
        configuration_directory_path: Path | None = None,
        *,
        locale: str | None = None,
    ):
        if configuration_directory_path is None:
            deprecate(
                f"Initializing {type(self)} without a configuration directory path is deprecated as of Betty 0.3.3, and will be removed in Betty 0.4.x.",
                stacklevel=2,
            )
            configuration_directory_path = CONFIGURATION_DIRECTORY_PATH
        super().__init__()
        self._configuration_directory_path = configuration_directory_path
        self._locale: str | None = locale

    @override
    @property
    def configuration_file_path(self) -> Path:
        return self._configuration_directory_path / "app.json"

    @configuration_file_path.setter
    def configuration_file_path(self, __: Path) -> None:
        pass

    @configuration_file_path.deleter
    def configuration_file_path(self) -> None:
        pass

    @property
    def locale(self) -> str | None:
        """
        The application locale.
        """
        return self._locale

    @locale.setter
    def locale(self, locale: str) -> None:
        try:
            get_data(locale)
        except ValueError:
            raise AssertionFailed(
                Str._(
                    '"{locale}" is not a valid IETF BCP 47 language tag.',
                    locale=locale,
                )
            ) from None
        self._locale = locale

    @override
    def update(self, other: Self) -> None:
        self._locale = other._locale

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField("locale", assert_str() | assert_setattr(self, "locale"))
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return minimize({"locale": void_none(self.locale)}, True)


@final
class App(Configurable[AppConfiguration]):
    """
    The Betty application.
    """

    def __init__(
        self,
        configuration: AppConfiguration,
        cache_directory_path: Path,
        project: Project | None = None,
    ):
        super().__init__()
        self._started = False
        self._configuration = configuration
        self._assets: AssetRepository | None = None
        self._extensions = _AppExtensions()
        self._extensions_initialized = False
        self._localization_initialized = False
        self._localizer: Localizer | None = None
        self._localizers: LocalizerRepository | None = None
        with suppress(FileNotFoundError):
            wait_to_thread(self.configuration.read())
        self._project = project or Project()
        # @todo How to update the extensions before the PR to decouple core components?
        # self.project.configuration.extensions.on_change(self._update_extensions)

        self._dispatcher: ExtensionDispatcher | None = None
        self._entity_types: set[type[Entity]] | None = None
        self._event_types: set[type[EventType]] | None = None
        self._url_generator: LocalizedUrlGenerator | None = None
        self._static_url_generator: StaticUrlGenerator | None = None
        self._jinja2_environment: Environment | None = None
        self._renderer: Renderer | None = None
        self._http_client: aiohttp.ClientSession | None = None
        self._fetcher: Fetcher | None = None
        self._cache_directory_path = cache_directory_path
        self._cache: Cache[Any] | None = None
        self._binary_file_cache: BinaryFileCache | None = None
        self._process_pool: Executor | None = None
        self._exit_stack = AsyncExitStack()

    @classmethod
    @asynccontextmanager
    async def new_from_environment(
        cls,
        *,
        project: Project | None = None,
    ) -> AsyncIterator[Self]:
        """
        Create a new application from the environment.
        """
        yield cls(
            AppConfiguration(CONFIGURATION_DIRECTORY_PATH),
            Path(environ.get("BETTY_CACHE_DIRECTORY", HOME_DIRECTORY_PATH / "cache")),
            project,
        )

    @classmethod
    @asynccontextmanager
    async def new_from_app(
        cls,
        app: App,
        *,
        project: Project | None = None,
    ) -> AsyncIterator[Self]:
        """
        Create a new application from an existing application.
        """
        yield cls(
            AppConfiguration(app.configuration._configuration_directory_path),
            app._cache_directory_path,
            app.project if project is None else project,
        )

    @classmethod
    @asynccontextmanager
    async def new_temporary(
        cls,
        *,
        project: Project | None = None,
    ) -> AsyncIterator[Self]:
        """
        Creat a new, temporary, isolated application.

        The application will not use any persistent caches, or leave
        any traces on the system.
        """
        async with (
            TemporaryDirectory() as configuration_directory_path_str,
            TemporaryDirectory() as cache_directory_path_str,
        ):
            yield cls(
                AppConfiguration(Path(configuration_directory_path_str)),
                Path(cache_directory_path_str),
                project,
            )

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()

    async def start(self) -> None:
        """
        Start the application.
        """
        if self._started:
            raise RuntimeError("This app has started already.")
        self._started = True

    async def stop(self) -> None:
        """
        Stop the application.
        """
        await self._exit_stack.aclose()
        self._started = False

    def __del__(self) -> None:
        if self._started:
            raise RuntimeError(f"{self} was started, but never stopped.")

    @property
    def project(self) -> Project:
        """
        The project.
        """
        return self._project

    def discover_extension_types(self) -> set[type[Extension]]:
        """
        Discover the available extension types.
        """
        from betty.app import extension

        return {
            *extension.discover_extension_types(),
            *map(type, self._extensions.flatten()),
        }

    @property
    def extensions(self) -> Extensions:
        """
        The enabled extensions.
        """
        if not self._extensions_initialized:
            self._extensions_initialized = True
            self._update_extensions()

        return self._extensions

    def _update_extensions(self) -> None:
        extension_types_enabled_in_configuration = set()
        for (
            app_extension_configuration
        ) in self.project.configuration.extensions.values():
            if app_extension_configuration.enabled:
                app_extension_configuration.extension_type.enable_requirement().assert_met()
                extension_types_enabled_in_configuration.add(
                    app_extension_configuration.extension_type
                )

        extension_types_sorter = TopologicalSorter(
            build_extension_type_graph(extension_types_enabled_in_configuration)
        )
        try:
            extension_types_sorter.prepare()
        except CycleError:
            raise CyclicDependencyError(
                [
                    app_extension_configuration.extension_type
                    for app_extension_configuration in self.project.configuration.extensions.values()
                ]
            ) from None

        extensions = []
        while extension_types_sorter.is_active():
            extension_types_batch = extension_types_sorter.get_ready()
            extensions_batch = []
            for extension_type in extension_types_batch:
                if (
                    issubclass(extension_type, ConfigurableExtension)
                    and extension_type in self.project.configuration.extensions
                ):
                    extension: Extension = extension_type(
                        self,
                        configuration=self.project.configuration.extensions[
                            extension_type
                        ].extension_configuration,
                    )
                else:
                    extension = extension_type(self)
                extensions_batch.append(extension)
                extension_types_sorter.done(extension_type)
            extensions.append(
                sorted(extensions_batch, key=lambda extension: extension.name())
            )
        self._extensions._update(extensions)
        del self.entity_types
        del self.event_types

    @property
    def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        if self._assets is None:
            assets = AssetRepository()
            assets.prepend(fs.ASSETS_DIRECTORY_PATH, "utf-8")
            for extension in self.extensions.flatten():
                extension_assets_directory_path = extension.assets_directory_path()
                if extension_assets_directory_path is not None:
                    assets.prepend(extension_assets_directory_path, "utf-8")
            assets.prepend(self.project.configuration.assets_directory_path)
            self._assets = assets
        return self._assets

    @property
    def dispatcher(self) -> Dispatcher:
        """
        The event dispatcher.
        """
        if self._dispatcher is None:
            self._dispatcher = ExtensionDispatcher(self.extensions)

        return self._dispatcher

    @property
    def url_generator(self) -> LocalizedUrlGenerator:
        """
        The (localized) URL generator.
        """
        from betty.url import AppUrlGenerator

        if self._url_generator is None:
            self._url_generator = AppUrlGenerator(self)
        return self._url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        """
        The static URL generator.
        """
        from betty.url import StaticPathUrlGenerator

        if self._static_url_generator is None:
            self._static_url_generator = StaticPathUrlGenerator(
                self.project.configuration
            )
        return self._static_url_generator

    @property
    def localizer(self) -> Localizer:
        """
        Get the application's localizer.
        """
        if self._localizer is None:
            self._localizer = wait_to_thread(
                self.localizers.get_negotiated(
                    self.configuration.locale or DEFAULT_LOCALE
                )
            )
        return self._localizer

    @property
    def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        if self._localizers is None:
            self._localizers = LocalizerRepository(self.assets)
        return self._localizers

    @property
    def jinja2_environment(self) -> Environment:
        """
        The Jinja2 environment.
        """
        if not self._jinja2_environment:
            from betty.jinja2 import Environment

            self._jinja2_environment = Environment(self)

        return self._jinja2_environment

    @property
    def renderer(self) -> Renderer:
        """
        The (file) content renderer.
        """
        if not self._renderer:
            from betty.jinja2 import Jinja2Renderer

            self._renderer = SequentialRenderer(
                [
                    Jinja2Renderer(self.jinja2_environment, self.project.configuration),
                ]
            )

        return self._renderer

    @property
    def http_client(self) -> aiohttp.ClientSession:
        """
        The HTTP client.
        """
        if not self._http_client:
            self._http_client = wait_to_thread(
                self._exit_stack.enter_async_context(
                    aiohttp.ClientSession(
                        connector=aiohttp.TCPConnector(limit_per_host=5),
                        headers={
                            "User-Agent": f"Betty (https://github.com/bartfeenstra/betty) on behalf of {self._project.configuration.base_url}{self._project.configuration.root_path}",
                        },
                    )
                )
            )
        return self._http_client

    @property
    def fetcher(self) -> Fetcher:
        """
        The fetcher.
        """
        if self._fetcher is None:
            self._fetcher = Fetcher(
                self.http_client,
                self.cache.with_scope("fetch"),
                self.binary_file_cache.with_scope("fetch"),
            )
        return self._fetcher

    @property
    def entity_types(self) -> set[type[Entity]]:
        """
        The available entity types.
        """
        if self._entity_types is None:
            from betty.model.ancestry import (
                Citation,
                Enclosure,
                Event,
                File,
                Note,
                Person,
                PersonName,
                Presence,
                Place,
                Source,
            )

            self._entity_types = reduce(
                operator.or_,
                wait_to_thread(self.dispatcher.dispatch(EntityTypeProvider)()),
                set(),
            ) | {
                Citation,
                Enclosure,
                Event,
                File,
                Note,
                Person,
                PersonName,
                Presence,
                Place,
                Source,
            }
        return self._entity_types

    @entity_types.deleter
    def entity_types(self) -> None:
        self._entity_types = None

    @property
    def event_types(self) -> set[type[EventType]]:
        """
        The available event types.
        """
        if self._event_types is None:
            self._event_types = set(
                wait_to_thread(self.dispatcher.dispatch(EventTypeProvider)())
            ) | {
                Birth,
                Baptism,
                Adoption,
                Death,
                Funeral,
                Cremation,
                Burial,
                Will,
                Engagement,
                Marriage,
                MarriageAnnouncement,
                Divorce,
                DivorceAnnouncement,
                Residence,
                Immigration,
                Emigration,
                Occupation,
                Retirement,
                Correspondence,
                Confirmation,
            }
        return self._event_types

    @event_types.deleter
    def event_types(self) -> None:
        self._event_types = None

    @property
    def cache(self) -> Cache[Any]:
        """
        The cache.
        """
        if self._cache is None:
            self._cache = PickledFileCache[Any](
                self.localizer, self._cache_directory_path
            )
        return self._cache

    @property
    def binary_file_cache(self) -> BinaryFileCache:
        """
        The binary file cache.
        """
        if self._binary_file_cache is None:
            self._binary_file_cache = BinaryFileCache(
                self.localizer, self._cache_directory_path
            )
        return self._binary_file_cache

    @property
    def process_pool(self) -> Executor:
        """
        The shared process pool.

        Use this to run CPU/computationally-heavy tasks in other processes.
        """
        if self._process_pool is None:
            # Avoid `fork` so as not to start worker processes with unneeded resources.
            # Settle for `spawn` so all environments use the same start method.
            self._process_pool = ProcessPoolExecutor(mp_context=get_context("spawn"))
        return self._process_pool
