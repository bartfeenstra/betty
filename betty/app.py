"""Define Betty's core application functionality."""

from __future__ import annotations

from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import asynccontextmanager
from multiprocessing import get_context
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Self, Any, final

import aiohttp
from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

from betty import fs
from betty.assertion import (
    OptionalField,
    assert_record,
    assert_setattr,
    assert_str,
)
from betty.assertion.error import AssertionFailed
from betty.assets import AssetRepository
from betty.asyncio import wait_to_thread
from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.cache.no_op import NoOpCache
from betty.config import Configurable, Configuration, assert_configuration_file
from betty.core import CoreComponent
from betty.fetch import Fetcher
from betty.fs import HOME_DIRECTORY_PATH
from betty.locale import get_data, DEFAULT_LOCALE
from betty.locale.localizable import _
from betty.locale.localizer import Localizer, LocalizerRepository
from betty.serde.dump import minimize, void_none, Dump, VoidableDump

if TYPE_CHECKING:
    from betty.cache import Cache
    from collections.abc import AsyncIterator, Callable

CONFIGURATION_DIRECTORY_PATH = fs.HOME_DIRECTORY_PATH / "configuration"


@final
class AppConfiguration(Configuration):
    """
    Provide configuration for :py:class:`betty.app.App`.
    """

    def __init__(
        self,
        *,
        locale: str | None = None,
    ):
        super().__init__()
        self._locale: str | None = locale

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
                _('"{locale}" is not a valid IETF BCP 47 language tag.').format(
                    locale=locale
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
        *,
        cache_factory: Callable[[Self], Cache[Any]],
    ):
        super().__init__()
        self._configuration = configuration
        self._assets: AssetRepository | None = None
        self._localization_initialized = False
        self._localizer: Localizer | None = None
        self._localizers: LocalizerRepository | None = None
        self._http_client: aiohttp.ClientSession | None = None
        self._fetcher: Fetcher | None = None
        self._cache_directory_path = cache_directory_path
        self._cache: Cache[Any] | None = None
        self._cache_factory = cache_factory
        self._binary_file_cache: BinaryFileCache | None = None
        self._process_pool: Executor | None = None

    @classmethod
    @asynccontextmanager
    async def new_from_environment(cls) -> AsyncIterator[Self]:
        """
        Create a new application from the environment.
        """
        configuration = AppConfiguration()
        configuration_file_path = CONFIGURATION_DIRECTORY_PATH / "app.json"
        if configuration_file_path.exists():
            assert_configuration_file(configuration)(configuration_file_path)
        yield cls(
            configuration,
            Path(environ.get("BETTY_CACHE_DIRECTORY", HOME_DIRECTORY_PATH / "cache")),
            cache_factory=lambda app: PickledFileCache[Any](
                app.localizer, app._cache_directory_path
            ),
        )

    @classmethod
    @asynccontextmanager
    async def new_temporary(cls) -> AsyncIterator[Self]:
        """
        Creat a new, temporary, isolated application.

        The application will not use any persistent caches, or leave
        any traces on the system.
        """
        async with (
            TemporaryDirectory() as cache_directory_path_str,
        ):
            yield cls(
                AppConfiguration(),
                Path(cache_directory_path_str),
                cache_factory=lambda app: NoOpCache(),
            )

    @property
    def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        if self._assets is None:
            self._assert_bootstrapped()
            self._assets = AssetRepository(fs.ASSETS_DIRECTORY_PATH)
        return self._assets

    @property
    def localizer(self) -> Localizer:
        """
        Get the application's localizer.
        """
        if self._localizer is None:
            self._assert_bootstrapped()
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
            self._assert_bootstrapped()
            self._localizers = LocalizerRepository(self.assets)
        return self._localizers

    @property
    def http_client(self) -> aiohttp.ClientSession:
        """
        The HTTP client.
        """
        if self._http_client is None:
            self._assert_bootstrapped()
            self._http_client = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit_per_host=5),
                headers={
                    "User-Agent": "Betty (https://github.com/bartfeenstra/betty)",
                },
            )
            wait_to_thread(
                self._async_exit_stack.enter_async_context(self._http_client)
            )
        return self._http_client

    @property
    def fetcher(self) -> Fetcher:
        """
        The fetcher.
        """
        if self._fetcher is None:
            self._assert_bootstrapped()
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
            self._assert_bootstrapped()
            self._cache = self._cache_factory(self)
        return self._cache

    @property
    def binary_file_cache(self) -> BinaryFileCache:
        """
        The binary file cache.
        """
        if self._binary_file_cache is None:
            self._assert_bootstrapped()
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
            self._assert_bootstrapped()
            # Avoid `fork` so as not to start worker processes with unneeded resources.
            # Settle for `spawn` so all environments use the same start method.
            self._process_pool = ProcessPoolExecutor(mp_context=get_context("spawn"))
        return self._process_pool
