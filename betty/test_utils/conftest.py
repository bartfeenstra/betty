"""
Betty/pytest test utilities.

Add ``from betty.test_utils.conftest import *`` to your project's ``conftest.py``
to start using these utilities.
"""

from __future__ import annotations

__all__ = [
    "binary_file_cache",
    "http_client_mock",
    "new_temporary_app",
    "new_temporary_app_factory",
    "page",
    "process_pool",
]

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Protocol

import pytest
import pytest_asyncio
from aioresponses import aioresponses

from betty.app import App
from betty.cache.file import BinaryFileCache
from betty.exception import do_raise
from betty.multiprocessing import ProcessPoolExecutor
from betty.user import Verbosity

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator  # noqa I001
    from concurrent import futures
    from contextlib import AbstractAsyncContextManager
    from pathlib import Path

    from playwright.async_api import BrowserContext, Page

    from betty.cache import Cache
    from betty.console.command import CommandDefinition
    from betty.model import EntityDefinition
    from betty.plugin import PluginRepository
    from betty.project.extension import ExtensionDefinition
    from betty.render import RendererDefinition
    from betty.service import ServiceFactory
    from betty.user import User


@pytest.fixture(autouse=True)
def http_client_mock() -> Iterator[aioresponses]:
    """
    Mock HTTP responses.
    """
    with aioresponses() as _http_client_mock:
        yield _http_client_mock


@pytest.fixture
async def binary_file_cache(tmp_path: Path) -> BinaryFileCache:
    """
    Create a temporary binary file cache.
    """
    return BinaryFileCache(tmp_path)


@pytest.fixture(scope="session")
async def process_pool() -> AsyncIterator[futures.ProcessPoolExecutor]:
    """
    Create a new, temporary :py:class:`betty.app.App`.
    """
    with ProcessPoolExecutor() as process_pool:
        yield process_pool


def _configure_new_temporary_app(app: App) -> None:
    app.user.verbosity = Verbosity.QUIET


@pytest.fixture
async def new_temporary_app(
    process_pool: futures.ProcessPoolExecutor,
) -> AsyncIterator[App]:
    """
    Create a new, temporary :py:class:`betty.app.App`.
    """
    async with App.new_temporary(process_pool=process_pool) as app:
        _configure_new_temporary_app(app)
        async with app:
            yield app


class NewTemporaryAppFactory(Protocol):
    def __call__(
        self,
        *,
        process_pool: futures.ProcessPoolExecutor | None = None,
        user: User | None = None,
        entity_type_repository: PluginRepository[EntityDefinition] | None = None,
        extension_repository: PluginRepository[ExtensionDefinition] | None = None,
        command_repository: PluginRepository[CommandDefinition] | None = None,
        renderer_repository: PluginRepository[RendererDefinition] | None = None,
    ) -> AbstractAsyncContextManager[App]:
        pass


@pytest.fixture
def new_temporary_app_factory(
    process_pool: futures.ProcessPoolExecutor,
) -> NewTemporaryAppFactory:
    """
    Get a factory to create a new, temporary :py:class:`betty.app.App`.
    """
    fixture_process_pool = process_pool

    @asynccontextmanager
    async def _new_temporary_app_factory(
        *,
        cache_factory: ServiceFactory[App, Cache[Any]] | None = None,
        process_pool: futures.ProcessPoolExecutor | None = None,
        user: User | None = None,
        entity_type_repository: PluginRepository[EntityDefinition] | None = None,
        extension_repository: PluginRepository[ExtensionDefinition] | None = None,
        command_repository: PluginRepository[CommandDefinition] | None = None,
        renderer_repository: PluginRepository[RendererDefinition] | None = None,
    ) -> AsyncIterator[App]:
        async with App.new_temporary(
            cache_factory=cache_factory,
            process_pool=process_pool or fixture_process_pool,
            user=user,
            entity_type_repository=entity_type_repository,
            extension_repository=extension_repository,
            command_repository=command_repository,
            renderer_repository=renderer_repository,
        ) as app:
            _configure_new_temporary_app(app)
            yield app

    return _new_temporary_app_factory


@pytest_asyncio.fixture(loop_scope="session")
async def page(context: BrowserContext) -> Page:
    """
    A Playwright Page instance.
    """
    page = await context.new_page()
    page.on("pageerror", do_raise)
    return page
