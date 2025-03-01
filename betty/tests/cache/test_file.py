import multiprocessing
from collections.abc import Sequence, AsyncIterator, Iterator
from contextlib import asynccontextmanager
from multiprocessing.managers import SyncManager
from pathlib import Path
from typing import Any

import pytest
from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

from betty.cache.file import PickledFileCache, BinaryFileCache
from betty.test_utils.cache import ProcesssafeCacheTestBase


class TestPickledFileCache(ProcesssafeCacheTestBase[Any]):
    @override
    @asynccontextmanager
    async def _new_sut(
        self,
        *,
        scopes: Sequence[str] | None = None,
    ) -> AsyncIterator[PickledFileCache[Any]]:
        async with TemporaryDirectory() as cache_directory_path_str:
            with multiprocessing.Manager() as manager:
                yield PickledFileCache(
                    Path(cache_directory_path_str), scopes=scopes, manager=manager
                )

    @override
    def _values(self) -> Iterator[Any]:
        yield True
        yield None
        yield 123
        yield 123.456
        yield []
        yield {}


class TestBinaryFileCache(ProcesssafeCacheTestBase[bytes]):
    @override
    @asynccontextmanager
    async def _new_sut(
        self,
        *,
        scopes: Sequence[str] | None = None,
    ) -> AsyncIterator[BinaryFileCache]:
        async with TemporaryDirectory() as cache_directory_path_str:
            with multiprocessing.Manager() as manager:
                yield BinaryFileCache(
                    Path(cache_directory_path_str), scopes=scopes, manager=manager
                )

    @override
    def _values(self) -> Iterator[bytes]:
        yield b"SomeBytes"

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    def test_path(
        self,
        multiprocessing_manager: SyncManager,
        scopes: Sequence[str],
        tmp_path: Path,
    ) -> None:
        sut = BinaryFileCache(
            Path(tmp_path), scopes=scopes, manager=multiprocessing_manager
        )
        assert sut.path == tmp_path.joinpath(*scopes)

    @pytest.mark.parametrize(
        ("expected_path_components", "scopes"),
        [
            (("b80bb7740288fda1f201890375a60c8f",), ()),
            (
                (
                    "scopey",
                    "dopey",
                    "b80bb7740288fda1f201890375a60c8f",
                ),
                (
                    "scopey",
                    "dopey",
                ),
            ),
        ],
    )
    def test_cache_item_file_path(
        self,
        expected_path_components: Sequence[str],
        multiprocessing_manager: SyncManager,
        scopes: Sequence[str],
        tmp_path: Path,
    ) -> None:
        sut = BinaryFileCache(
            Path(tmp_path), scopes=scopes, manager=multiprocessing_manager
        )
        assert sut.cache_item_file_path("id") == tmp_path.joinpath(
            *expected_path_components
        )
