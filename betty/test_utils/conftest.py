"""
Betty/pytest test utilities.

Add ``from betty.test_utils.conftest import *`` to your project's ``conftest.py``
to start using these utilities.
"""

from __future__ import annotations

__all__ = [
    "binary_file_cache",
    "multiprocessing_manager",
    "new_temporary_app",
    "new_temporary_app_factory",
    "page",
    "process_pool",
]

import multiprocessing
from typing import TYPE_CHECKING, Any, Protocol

import pytest
import pytest_asyncio

from betty.app import App
from betty.cache.file import BinaryFileCache
from betty.error import do_raise
from betty.multiprocessing import ProcessPoolExecutor

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator  # noqa I001
    from concurrent import futures
    from contextlib import AbstractAsyncContextManager
    from multiprocessing.managers import SyncManager
    from pathlib import Path

    from betty.cache import Cache
    from betty.fetch import Fetcher
    from betty.service import ServiceFactory
    from playwright.async_api import BrowserContext, Page


@pytest.fixture
async def binary_file_cache(
    multiprocessing_manager: SyncManager, tmp_path: Path
) -> BinaryFileCache:
    """
    Create a temporary binary file cache.
    """
    return BinaryFileCache(tmp_path, manager=multiprocessing_manager)


@pytest.fixture(scope="session")
async def process_pool() -> AsyncIterator[futures.ProcessPoolExecutor]:
    """
    Create a new, temporary :py:class:`betty.app.App`.
    """
    with ProcessPoolExecutor() as process_pool:
        yield process_pool


@pytest.fixture(scope="session")
def multiprocessing_manager() -> Iterator[SyncManager]:
    """
    Raise Betty's own deprecation warnings as errors.
    """
    with multiprocessing.Manager() as manager:
        yield manager


@pytest.fixture
async def new_temporary_app(
    process_pool: futures.ProcessPoolExecutor, multiprocessing_manager: SyncManager
) -> AsyncIterator[App]:
    """
    Create a new, temporary :py:class:`betty.app.App`.
    """
    async with (
        App.new_temporary(
            process_pool=process_pool, multiprocessing_manager=multiprocessing_manager
        ) as app,
        app,
    ):
        yield app


class NewTemporaryAppFactory(Protocol):
    async def __call__(
        self,
        *,
        fetcher: Fetcher | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
    ) -> AbstractAsyncContextManager[App]:
        pass


@pytest.fixture
async def new_temporary_app_factory(
    process_pool: futures.ProcessPoolExecutor, multiprocessing_manager: SyncManager
) -> NewTemporaryAppFactory:
    """
    Get a factory to create a new, temporary :py:class:`betty.app.App`.
    """
    fixture_process_pool = process_pool
    fixture_multiprocessing_manager = multiprocessing_manager

    async def _new_temporary_app_factory(
        *,
        cache_factory: ServiceFactory[App, Cache[Any]] | None = None,
        fetcher: Fetcher | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
        multiprocessing_manager: SyncManager | None = None,
    ) -> AbstractAsyncContextManager[App]:
        return App.new_temporary(
            cache_factory=cache_factory,
            fetcher=fetcher,
            process_pool=process_pool or fixture_process_pool,
            multiprocessing_manager=multiprocessing_manager
            or fixture_multiprocessing_manager,
        )

    return _new_temporary_app_factory


@pytest_asyncio.fixture(loop_scope="session")
async def page(context: BrowserContext) -> Page:
    """
    A Playwright Page instance.
    """
    page = await context.new_page()
    page.on("pageerror", do_raise)
    return page
