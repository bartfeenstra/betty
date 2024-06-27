"""Define Betty's core application functionality."""

from __future__ import annotations

from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import suppress, asynccontextmanager
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
from betty.core import CoreComponent
from betty.fetch import Fetcher
from betty.fs import HOME_DIRECTORY_PATH
from betty.locale import LocalizerRepository, get_data, DEFAULT_LOCALE, Localizer, Str
from betty.model import Entity
from betty.model.event_type import (
    EventType,
)
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
    from collections.abc import AsyncIterator

CONFIGURATION_DIRECTORY_PATH = fs.HOME_DIRECTORY_PATH / "configuration"


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
class App(Configurable[AppConfiguration], CoreComponent):
    """
    The Betty application.
    """

    def __init__(
        self,
        configuration: AppConfiguration,
        cache_directory_path: Path,
    ):
        super().__init__()
        self._configuration = configuration
        self._localization_initialized = False
        self._localizer: Localizer | None = None
        self._localizers: LocalizerRepository | None = None
        with suppress(FileNotFoundError):
            wait_to_thread(self.configuration.read())
        # @todo How to update the extensions before the PR to decouple core components?
        # self.project.configuration.extensions.on_change(self._update_extensions)

        self._entity_types: set[type[Entity]] | None = None
        self._event_types: set[type[EventType]] | None = None
        self._http_client: aiohttp.ClientSession | None = None
        self._fetcher: Fetcher | None = None
        self._cache_directory_path = cache_directory_path
        self._cache: Cache[Any] | None = None
        self._binary_file_cache: BinaryFileCache | None = None
        self._process_pool: Executor | None = None

    @classmethod
    @asynccontextmanager
    async def new_from_environment(cls, /) -> AsyncIterator[Self]:
        """
        Create a new application from the environment.
        """
        yield cls(
            AppConfiguration(CONFIGURATION_DIRECTORY_PATH),
            Path(environ.get("BETTY_CACHE_DIRECTORY", HOME_DIRECTORY_PATH / "cache")),
        )

    @classmethod
    @asynccontextmanager
    async def new_from_app(cls, app: App, /) -> AsyncIterator[Self]:
        """
        Create a new application from an existing application.
        """
        yield cls(
            AppConfiguration(app.configuration._configuration_directory_path),
            app._cache_directory_path,
        )

    @classmethod
    @asynccontextmanager
    async def new_temporary(cls, /) -> AsyncIterator[Self]:
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
            )

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
                            "User-Agent": "Betty (https://github.com/bartfeenstra/betty)",
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
