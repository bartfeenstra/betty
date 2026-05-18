from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from json import dumps
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.caches.file import PickledFileCache
from betty.file import write
from betty.project import Project, ProjectData
from betty.test_utils.conftest import IsolatedAppFactory, IsolatedProjectFactory
from betty.test_utils.console import run
from betty.test_utils.user import StaticUser
from betty.user import User

type AssertAppCacheDirectories = Callable[
    [bool, User | None], AbstractAsyncContextManager[App]
]
type AssertProjectCacheDirectories = Callable[
    [bool, App], AbstractAsyncContextManager[Project]
]


class TestClearCaches:
    @pytest.fixture
    def assert_app_cache_directories(
        self,
        isolated_app_factory: IsolatedAppFactory,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> AssertAppCacheDirectories:
        @asynccontextmanager
        async def _assert_app_cache_directories(
            expected: bool, user: User | None = None, /
        ) -> AsyncIterator[App]:
            app_cache_directory = tmp_path / "app-cache"

            app_binary_file_cache_directory = tmp_path / "app-binary-file-cache"

            tmp_path / "project"

            legacy_cache_directory = tmp_path / "legacy-cache"
            legacy_cache_directory.mkdir()
            mocker.patch(
                "betty.plugins.command.clear_caches._LEGACY_CACHE_DIRECTORY",
                legacy_cache_directory,
            )
            legacy_cache_item = legacy_cache_directory / "item"
            legacy_cache_item.touch()

            async with isolated_app_factory(
                binary_file_cache_directory=app_binary_file_cache_directory,
                cache=PickledFileCache(app_cache_directory),
                user=user,
            ) as app:
                cache_item_key = "my-first-app-cache-item"
                binary_file_cache_item_key = "my-first-app-binary-file-cache-item"

                await app.cache.set(cache_item_key, "My First App Cache Item")
                assert await app.cache.has(cache_item_key)
                await app.binary_file_cache.set(
                    binary_file_cache_item_key, b"My First App Binary File Cache Item"
                )
                assert await app.binary_file_cache.has(binary_file_cache_item_key)

                yield app

                assert await app.cache.has(cache_item_key) is expected
                assert (
                    await app.binary_file_cache.has(binary_file_cache_item_key)
                    is expected
                )
            assert legacy_cache_item.exists() is expected

        return _assert_app_cache_directories

    @pytest.fixture
    def assert_project_cache_directories(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> AssertProjectCacheDirectories:
        @asynccontextmanager
        async def _assert_project_cache_directories(
            expected: bool, app: App, /
        ) -> AsyncIterator[Project]:
            project_directory = tmp_path / "project"

            project_directory.mkdir()
            await write(
                project_directory / "betty.json",
                dumps(
                    ProjectData.data().porter.dump(
                        ProjectData(title="Betty", url="https://example.com")
                    )
                ),
            )

            async with isolated_project_factory(
                app=app, cache=None, directory=project_directory
            ) as project:
                cache_item_key = "my-first-project-cache-item"
                binary_file_cache_item_key = "my-first-project-binary-file-cache-item"

                await project.cache.set(cache_item_key, "My First Project Cache Item")
                assert await project.cache.has(cache_item_key)
                await project.binary_file_cache.set(
                    binary_file_cache_item_key,
                    b"My First Project Binary File Cache Item",
                )
                assert await project.binary_file_cache.has(binary_file_cache_item_key)

                yield project

                assert await project.cache.has(cache_item_key) is expected
                assert (
                    await project.binary_file_cache.has(binary_file_cache_item_key)
                    is expected
                )

        return _assert_project_cache_directories

    async def test_configure__without_confirmation(
        self, assert_app_cache_directories: AssertAppCacheDirectories
    ) -> None:
        user = StaticUser(confirmations=[False])
        async with assert_app_cache_directories(True, user) as app:
            await run(app, "clear-caches")

    async def test_configure__with_confirmation(
        self, assert_app_cache_directories: AssertAppCacheDirectories
    ) -> None:
        user = StaticUser(confirmations=[True])
        async with assert_app_cache_directories(False, user) as app:
            await run(app, "clear-caches")

    async def test_configure__with_yes(
        self, assert_app_cache_directories: AssertAppCacheDirectories
    ) -> None:
        async with assert_app_cache_directories(False, None) as app:
            await run(app, "clear-caches", "--yes")

    async def test_configure__with_project_without_confirmation(
        self,
        assert_app_cache_directories: AssertAppCacheDirectories,
        assert_project_cache_directories: AssertProjectCacheDirectories,
    ) -> None:
        user = StaticUser(confirmations=[False])
        async with (
            assert_app_cache_directories(True, user) as app,
            assert_project_cache_directories(True, app) as project,
        ):
            await run(
                app, "clear-caches", "--project", str(project.directory / "betty.json")
            )

    async def test_configure__with_project_with_confirmation(
        self,
        assert_app_cache_directories: AssertAppCacheDirectories,
        assert_project_cache_directories: AssertProjectCacheDirectories,
    ) -> None:
        user = StaticUser(confirmations=[True])
        async with (
            assert_app_cache_directories(False, user) as app,
            assert_project_cache_directories(False, app) as project,
        ):
            await run(
                app, "clear-caches", "--project", str(project.directory / "betty.json")
            )

    async def test_configure__with_project_with_yes(
        self,
        assert_app_cache_directories: AssertAppCacheDirectories,
        assert_project_cache_directories: AssertProjectCacheDirectories,
    ) -> None:
        async with (
            assert_app_cache_directories(False, None) as app,
            assert_project_cache_directories(False, app) as project,
        ):
            await run(
                app,
                "clear-caches",
                "--yes",
                "--project",
                str(project.directory / "betty.json"),
            )
